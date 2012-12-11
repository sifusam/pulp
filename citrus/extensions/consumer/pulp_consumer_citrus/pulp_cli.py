# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

from gettext import gettext as _

from pulp.client.extensions.extensions import PulpCliSection
from bind import BindCommand, UnbindCommand
from content import ContentSection

# -- framework hook -----------------------------------------------------------

def initialize(context):
    parent_section = PulpCliSection('citrus', 'citrus commands')
    parent_section.add_subsection(ContentSection(context))
    m = 'binds a downsteam pulp server to a repository'
    parent_section.add_command(BindCommand(context, 'bind', _(m)))
    m = 'removes the binding between a downstream pulp server and a repository'
    parent_section.add_command(UnbindCommand(context, 'unbind', _(m)))
    context.cli.add_section(parent_section)