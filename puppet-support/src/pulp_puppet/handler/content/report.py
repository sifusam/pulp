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

from pulp.agent.lib.report import HandlerReport


OP_INSTALL = 'install'
OP_UPDATE = 'update'
OP_UNINSTALL = 'uninstall'


class PuppetModuleOperationReport(object):
    """
    Tracks a puppet module operation (install, update, remove) and generates
    the standard representation of both the final report to be returned from
    the operation handler call and the progress report to be sent as the
    operation proceeds.
    """

    def __init__(self, conduit):
        """
        :param conduit: used to communicate back to the handler framework
        :type  conduit: pulp.agent.lib.conduit.Conduit
        """
        self.conduit = conduit

        # Keeps the state of each thing done in the operation being tracked.
        # These should only be added to using the state methods below to ensure
        # the correct format.
        self.installs = []
        self.updates = []
        self.uninstalls = []

    # -- state changes --------------------------------------------------------

    def success_installed_module(self, unit):


        # Format:
        # {
        #     'unit_request' : <unit passed from the server>,
        #     'unit_key' : <key of the actual unit installed>,
        #
        # }
        pass

    def failed_installed_module(self, unit):
        pass

    def success_updated_module(self, unit):
        pass

    def success_removed_module(self, unit):
        pass

    # -- progress reporting ---------------------------------------------------

    def send_progress(self):
        progress_report = self.to_progress_report()
        self.conduit.update_progress(progress_report)

    # -- report generation ----------------------------------------------------

    def to_final_report(self):
        final_report = HandlerReport()
        return final_report

    def to_progress_report(self):
        return
