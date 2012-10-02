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
Handles all content related requests for a puppet master.
"""

from pulp.agent.lib.handler import ContentHandler

from pulp_puppet.handler.content.report import PuppetModuleOperationReport
from pulp_puppet.handler.content import install


class PuppetMasterContentHandler(ContentHandler):

    def install(self, conduit, units, options):
        report = PuppetModuleOperationReport(conduit)

        installer = install.PuppetModuleInstaller(self.cfg, report, conduit)
        installer.install_modules(units, options)

        return report

    def uninstall(self, conduit, units, options):
        report = PuppetModuleOperationReport(conduit)

        return report

    def update(self, conduit, units, options):
        report = PuppetModuleOperationReport(conduit)

        return report
