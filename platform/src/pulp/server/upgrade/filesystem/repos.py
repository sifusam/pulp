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
import shutil
import yum
from pulp.server.upgrade.model import UpgradeStepReport
from pulp.server.upgrade.utils import PrestoParser

DIR_STORAGE_ROOT = '/var/lib/pulp/content/'
DIR_RPMS = os.path.join(DIR_STORAGE_ROOT, 'rpm')
DIR_SRPMS = os.path.join(DIR_STORAGE_ROOT, 'srpm')
DIR_DRPM = os.path.join(DIR_STORAGE_ROOT, 'drpm')
V1_DIR_RPMS = '/var/lib/pulp/packages/'

YUM_DISTRIBUTOR_TYPE_ID = 'yum_distributor'
YUM_DISTRIBUTOR_ID = YUM_DISTRIBUTOR_TYPE_ID

DISTRIBUTOR_REPO_WORKING_DIR = "/var/lib/pulp/working/repos/"

def upgrade(v1_database, v2_database):
    report = UpgradeStepReport()

    repo_success = _repos(v2_database, report)

    report.success = repo_success
    return report

def _repos(v2_database, report):
    """
    # - grab the repo_id and distributor id
    # - construct the distributor_working _path
    # - for each repoid get repo_content_units.find({'repoid' : 'repoid', 'unit_type_id' : 'rpms'})
    # grab the storage path from each unit,
    # symlink path = distributor_working_dir + unit_relative_path
    # create symlink path -> unit_storage_path
    """
    v2_dist_coll = v2_database.repo_distributors
    v2_repo_content_unit = v2_database.repo_content_units
    v2_rpms = v2_database.units_rpm
    v2_srpms = v2_database.units_srpm
    v2_drpms = v2_database.units_drpm
    v2_distro = v2_database.units_distribution

    repo_distributors = v2_dist_coll.find({'distributor_id' : 'yum_distributor'})
    for repo_dist in repo_distributors:
        repo_id, repo_distributor_id = repo_dist['repo_id'], repo_dist['distributor_type_id']
        distributor_working_dir = "%s/%s/distributors/%s" % (DISTRIBUTOR_REPO_WORKING_DIR, repo_id, repo_distributor_id)
        print "distributor working dir", distributor_working_dir
        for type_id in ['rpm', 'srpm', 'drpm', 'distribution']:
            spec={'repo_id' : repo_id, 'unit_type_id' : type_id}
            associated_units = v2_repo_content_unit.find(spec)
            print type_id #, type(list(units))
            for ass_unit in list(associated_units):
                unit = None
                if type_id == 'rpm':
                    unit = v2_rpms.find_one({'_id' : ass_unit['unit_id']})
                    if unit is None:
                        continue
                    rpm_rel_path =  "%s/%s/%s/%s/%s/%s" % (unit['name'], unit['version'], unit['release'],
                                                           unit['arch'], unit['checksum'], unit['filename'])
                    v2_pkgpath = os.path.join(DIR_RPMS, rpm_rel_path)
                elif type_id == 'srpm':
                    unit = v2_srpms.find_one({'_id' : ass_unit['unit_id']})
                    if unit is None:
                        continue
                    rpm_rel_path =  "%s/%s/%s/%s/%s/%s" % (unit['name'], unit['version'], unit['release'],
                                                           unit['arch'], unit['checksum'], unit['filename'])
                    v2_pkgpath = os.path.join(DIR_SRPMS, rpm_rel_path)
                if not os.path.exists(v2_pkgpath):
                    # missing source path, skip migrate
                    print "missing",v2_pkgpath
                    report.warning("Package %s does not exist" % v2_pkgpath)
                    continue
                unit_repo_symlink_path = os.path.join(distributor_working_dir, os.path.basename(v2_pkgpath))
                if not os.path.isdir(distributor_working_dir):
                    os.makedirs(distributor_working_dir)
                print v2_pkgpath, unit_repo_symlink_path
                os.symlink(v2_pkgpath, unit_repo_symlink_path)
                print "Symlink created from %s -> %s" % (unit_repo_symlink_path, v2_pkgpath)
#                elif type_id == 'drpm':
#                    unit = v2_drpms.find_one({'_id' : ass_unit['unit_id']})
#                elif type_id == 'distribution':
#                    unit = v2_distro.find_one({'_id' : ass_unit['unit_id']})

    return True