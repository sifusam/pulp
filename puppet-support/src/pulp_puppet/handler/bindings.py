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

from pulp.agent.lib.handler import BindHandler


class PuppetMasterBindingsHandler(BindHandler):
    
    def clean(self, conduit):
        return BindHandler.clean(self, conduit)

    def bind(self, conduit, definitions):
        return BindHandler.bind(self, conduit, definitions)

    def unbind(self, conduit, repoid):
        return BindHandler.unbind(self, conduit, repoid)

    def rebind(self, conduit, definitions):
        return BindHandler.rebind(self, conduit, definitions)
