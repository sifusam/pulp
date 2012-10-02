# Copyright (c) 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

"""
Performs the installation of a puppet module into a puppet master.

There are currently no supported options to this call. However, when there are,
the description of how to specify those options will be found here.
"""

from httplib import HTTPConnection, HTTPSConnection
import logging
import os
import shutil
import tarfile
import tempfile
import pycurl
import urlparse

from pulp.common.util import encode_unicode

from pulp_puppet.common import constants
from pulp_puppet.common.download import StoredDownloadedContent
from pulp_puppet.common.model import Module, RepositoryMetadata
from pulp_puppet.handler.model import BoundRepositoryFile


LOG = logging.getLogger(__name__)


class PuppetModuleInstaller(object):

    def __init__(self, config, report, conduit):
        """
        :param config: configuration for the handler as loaded by the framework
        :type  config: dict
        :param report: report instance to track the installation
        :type  report: pulp_puppet.handler.content.report.PuppetModuleOperationReport
        :param conduit: callback into the handler framework for progress reporting
        :type  conduit: pulp.agent.lib.conduit.Conduit
        """
        super(PuppetModuleInstaller, self).__init__()

        self.config = config
        self.report = report
        self.conduit = conduit

    def install_modules(self, units, options):
        """
        Performs any steps to ensure the given units are installed into the
        correct location. This call is idempotent and will handle the situation
        where a module is already installed (anything from a no-op to a
        verification of the module against the server).

        The report will be updated as appropriate by this call, including
        setting the overall state of the operation. The caller should return
        the report as is to the framework.

        This call will attempt to handle exceptions and will update the report
        to indicate which module failed. Any unexpected exceptions should be
        allowed to bubble up to the framework.

        The assumption is that each unit will be a full unit key for a module.
        In the event a user wanted to specify a partial unit key, it will be up
        to a puppet module profiler to translate before it gets to this handler.

        :param units: list of units to install; the format of these dict objects
               can be found in the _determine_module method
        :type  units: list
        :param options: arbitrary options passed from the user during the call;
               the format can be found in the module-level documentation
        """

        # Load all repository metadata
        bound_repo_files = self._load_bound_repo_files()
        bound_repos = []
        for bound_repo_file in bound_repo_files:
            r = self._retrieve_repository_metadata(bound_repo_file)
            bound_repos.append(r)

        # Resolve which repository a unit comes from
        module_install_requests = [ModuleInstallRequest.from_module(Module.from_dict(u)) for u in units]
        unfound_module_requests = []

        for request in module_install_requests:
            for bound_repo in bound_repos:
                if request.module in bound_repo.modules:
                    request.download_url = bound_repo.calculate_module_url(request.module)
                    break
            else:
                unfound_module_requests.append(request)

        # TODO: Handle the case where an install was requested for an unfound module

        # Download or ensure each file is downloaded into the expected location
        for request in module_install_requests:
            self._ensure_downloaded(request)

    # -- repository metadata retrieval ----------------------------------------

    def _load_bound_repo_files(self):
        repo_dir = self.config[constants.CONFIG_CONSUMER_REPO_DIR]

        bound_repos = []
        for repo_file in os.listdir(repo_dir):
            full_filename = os.path.join(repo_dir, repo_file)
            bound_repo = BoundRepositoryFile.load(full_filename)
            bound_repos.append(bound_repo)

        return bound_repos

    def _retrieve_repository_metadata(self, bound_repository_file):
        """

        :param bound_repository_file:
        :type  bound_repository_file: BoundRepositoryFile

        :return: list of information about modules within a bound repository
        :rtype:  list
        """

        headers = {'Accept': 'application/json',
                   'Content-Type': 'application/json'}

        if bound_repository_file.protocol == constants.PROTOCOL_HTTP:
            connection = HTTPConnection(bound_repository_file.host)
        else:
            connection = HTTPSConnection(bound_repository_file.host)

        # Generate the relative URL to the metadata file
        relative_url = '/'.join([bound_repository_file.repo_relative_url, constants.REPO_METADATA_FILENAME])

        LOG.info('Retrieving metadata file at <%s>' % relative_url)

        connection.request('GET', relative_url, headers=headers)

        response = connection.getresponse()
        response_body = response.read()

        # Use the common domain objects to parse the metadata JSON file
        repository_metadata = RepositoryMetadata()
        repository_metadata.update_from_json(response_body)

        br = BoundRepository(bound_repository_file.repo_id,
                             bound_repository_file.protocol,
                             bound_repository_file.host,
                             bound_repository_file.repo_relative_url,
                             repository_metadata.modules)

        return br

    # -- module installation --------------------------------------------------

    def _ensure_downloaded(self, module_install_request):
        """
        :param module_install_request:
        :type  module_install_request: ModuleInstallRequest
        """

        deploy_dir = self._module_deploy_dir(module_install_request)

        # Check to see if the module already exists.
        #
        # It's possible the logic below will only indicate a module of the
        # same name exists, but not necessarily the exact same module (for
        # instance, different authors).
        #
        # The "puppet module" command will barf saying it's a conflict. We
        # probably want to replicate that here, but for now assume it's already
        # installed and move on.

        if os.path.exists(deploy_dir):
            return

        tmp_file = self._download_module(module_install_request)
        self._install_module(module_install_request, tmp_file)

    def _download_module(self, module_install_request):
        """
        :param module_install_request:
        :type  module_install_request: ModuleInstallRequest
        """

        url = encode_unicode(module_install_request.download_url)
        tmp_file = tempfile.mktemp(prefix='pulp-puppet-install-')

        LOG.info('Downloading module at <%s>' % url)

        curl = pycurl.Curl()
        content = StoredDownloadedContent(tmp_file)
        content.open()
        try:
            curl.setopt(pycurl.VERBOSE, 0)
            curl.setopt(pycurl.LOW_SPEED_LIMIT, 1000)
            curl.setopt(pycurl.LOW_SPEED_TIME, 5 * 60)
            curl.setopt(pycurl.WRITEFUNCTION, content.update)
            curl.setopt(pycurl.URL, url)

            curl.perform()
            status = curl.getinfo(curl.HTTP_CODE)

            # TODO: Add in status checking to see if it downloaded correctly

            curl.close()
            content.close()
        except Exception, e:
            LOG.exception('Exception downloading module from <%s>' % url)

            curl.close()
            content.close()
            content.delete()
            raise

        return tmp_file

    def _install_module(self, module_install_request, tmp_file):

        LOG.info('Installing module from tarball <%s>' % tmp_file)

        # Extract everything to a temp directory first (we'll need to analyze
        # what comes out of the tarball.

        tmp_deploy_dir = tempfile.mkdtemp(prefix='pulp-puppet-install-')

        tarball = tarfile.open(tmp_file)
        tarball.extractall(path=tmp_deploy_dir)

        # Most modules seem to have a level of nesting in the module such that
        # everything is extracted to a directory first. That directory is not
        # named the same as puppet master wants, so we can't just extract the
        # tarball directoy to the puppet master dir. Look in the temp dir and
        # if there's only a single directory in there, only copy its contents
        # to the actual deploy directory. If there are multiple files, assume
        # the puppet module was packaged incorrectly and everything represents
        # the module contents and copy it all.

        copy_src_dir = tmp_deploy_dir
        if len(os.listdir(tmp_deploy_dir)) == 1:
            copy_src_dir = os.path.join(tmp_deploy_dir, os.listdir(tmp_deploy_dir)[0])

        deploy_dir = self._module_deploy_dir(module_install_request)
        shutil.copytree(copy_src_dir, deploy_dir)

        shutil.rmtree(tmp_deploy_dir)
        os.remove(tmp_file)

    def _module_deploy_dir(self, module_install_request):
        deploy_dir = os.path.join(self.config[constants.CONFIG_PUPPET_MASTER_DIR],
                                  module_install_request.name)
        return deploy_dir


class ModuleInstallRequest(object):
    """
    Contains the details of a single module that needs to be installed.
    """

    @classmethod
    def from_module(cls, module):
        """
        :param module: the standard domain representation of a module
        :type  module: pulp_puppet.common.model.Module
        """
        return cls(module)

    def __init__(self, module):
        self.module = module
        self.download_url = None

    @property
    def name(self):
        return self.module.name

    @property
    def version(self):
        return self.module.version

    @property
    def author(self):
        return self.module.author


class BoundRepository(object):
    """
    Contains a list of modules in a single bound repository and the base URL
    at which modules are downloaded from it.
    """

    def __init__(self, repo_id, protocol, host, repo_relative_url, modules):

        self.repo_id = repo_id
        self.protocol = protocol
        self.host = host
        self.repo_relative_url = repo_relative_url
        self.modules = modules

    def __str__(self):
        return 'Repo ID <%s> Relative URL <%s>' % (self.repo_id, self.repo_relative_url)

    def calculate_module_url(self, module):
        """
        Calculates the full URL to the given unit in this repository.

        :return:
        """
        module_relative_url = constants.HOSTED_MODULE_FILE_RELATIVE_PATH % (module.author[0], module.author)
        relative_url = '/'.join([self.repo_relative_url, module_relative_url, module.filename()])

        data = (self.protocol, self.host, relative_url, None, None)
        full_url = urlparse.urlunsplit(data)

        return full_url
