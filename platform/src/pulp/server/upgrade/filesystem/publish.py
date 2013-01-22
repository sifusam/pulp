# -*- coding: utf-8 -*-
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
from pulp.server.upgrade.model import UpgradeStepReport

DISTRIBUTOR_REPO_WORKING_DIR = "/var/lib/pulp/working/repos/"

def upgrade(v1_database, v2_database):
    report = UpgradeStepReport()

    repo_success = _publish(v2_database, report)

    report.success = repo_success
    return report

def _publish(v2_database, report):
    """
    Publish the repo to http/https by creating a symlink from
    distributor working dir to published dir. At this point the
    db, content and repo is fully upgraded to v2 and just waiting
    to be published"""
    pass
