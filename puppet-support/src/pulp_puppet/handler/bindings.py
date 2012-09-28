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

import os
import urlparse

from pulp.agent.lib.handler import BindHandler
from pulp.agent.lib.report import BindReport, CleanReport

from pulp_puppet.common import constants


class PuppetMasterBindingsHandler(BindHandler):
    def __init__(self, cfg):
        BindHandler.__init__(self, cfg)

        self.repo_dir = cfg[constants.CONFIG_CONSUMER_REPO_DIR]

    def clean(self, conduit):
        for f in os.listdir(self.repo_dir):
            filename = os.path.join(self.repo_dir, f)
            os.remove(filename)

        report = CleanReport()
        report.succeeded()
        return report

    def bind(self, conduit, definitions):

        for definition in definitions:
            details = definition['details']
            repository = definition['repository']
            repo_id = repository['id']

            self._write_repository_file(repo_id, details)

        report = BindReport()
        report.succeeded()
        return report

    def unbind(self, conduit, repo_id):
        self._delete_repository_file(repo_id)

        report = BindReport()
        report.succeeded()
        return report

    def rebind(self, conduit, definitions):
        # Bind simply replaces the definitions, which is the same behavior
        # a rebind should exhibit.
        self.bind(conduit, definitions)

        report = BindReport()
        report.succeeded()
        return report

    # -- private --------------------------------------------------------------

    def _write_repository_file(self, repo_id, details):
        # If there's already a definition, replace it
        filename = self._repository_file_path(repo_id)
        self._delete_repository_file(repo_id)

        # Collect data to write
        protocol = details[constants.PAYLOAD_PROTOCOL]
        host = details[constants.PAYLOAD_SERVER]

        repo_url = self._assemble_repo_url(protocol, host, repo_id)

        # Write out a repo definition
        f = open(filename, 'w')
        f.write(repo_url)
        f.write('\n')
        f.close()

    def _delete_repository_file(self, repo_id):
        # Determine full file path
        filename = self._repository_file_path(repo_id)

        if os.path.exists(filename):
            os.remove(filename)

    def _assemble_repo_url(self, protocol, host, repo_id):
        url = '/'.join([constants.WEB_ALIAS, repo_id])

        # scheme, netloc, url, params, query, fragment
        data = (protocol, host, url, None, None, None)
        repo_url = urlparse.urlunparse(data)
        return repo_url

    def _repository_file_path(self, repo_id):
        filename = os.path.join(self.repo_dir, repo_id)
        return filename
