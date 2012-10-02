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

from pulp.agent.lib.handler import BindHandler
from pulp.agent.lib.report import BindReport, CleanReport

from pulp_puppet.common import constants
from pulp_puppet.handler.model import BoundRepositoryFile


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

            bound_repo = BoundRepositoryFile(self.cfg, repo_id)
            bound_repo.update_from_binding(details)
            bound_repo.save()

        report = BindReport()
        report.succeeded()
        return report

    def unbind(self, conduit, repo_id):
        bound_repo = BoundRepositoryFile(self.cfg, repo_id)
        bound_repo.delete()

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
