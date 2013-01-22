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

DIR_STORAGE_ROOT = '/var/lib/pulp/content/'
DIR_RPMS = os.path.join(DIR_STORAGE_ROOT, 'rpm')
DIR_SRPMS = os.path.join(DIR_STORAGE_ROOT, 'srpm')
DIR_DRPM = os.path.join(DIR_STORAGE_ROOT, 'drpm')
DIR_DISTRO = os.path.join(DIR_STORAGE_ROOT, 'distributions')
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
    repo_distributors = v2_dist_coll.find({'distributor_type_id' : 'yum_distributor'})
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
                    unit_repo_symlink_path = os.path.join(distributor_working_dir, os.path.basename(v2_pkgpath))
                    _symlink_rpms(v2_pkgpath, unit_repo_symlink_path, report)
                elif type_id == 'srpm':
                    unit = v2_srpms.find_one({'_id' : ass_unit['unit_id']})
                    if unit is None:
                        continue
                    rpm_rel_path =  "%s/%s/%s/%s/%s/%s" % (unit['name'], unit['version'], unit['release'],
                                                           unit['arch'], unit['checksum'], unit['filename'])
                    v2_pkgpath = os.path.join(DIR_SRPMS, rpm_rel_path)
                    unit_repo_symlink_path = os.path.join(distributor_working_dir, os.path.basename(v2_pkgpath))
                    _symlink_rpms(v2_pkgpath, unit_repo_symlink_path, report)
                elif type_id == 'distribution':
                    unit = v2_distro.find_one({'_id' : ass_unit['unit_id']})
                    if unit is None:
                        continue
                    #v2_pkgpath = os.path.join(DIR_DISTRO, unit['id'])
                    #print "FFFFFFFFFFFFFF",v2_pkgpath
                    _symlink_distribution_files(unit, distributor_working_dir, report)
#                elif type_id == 'drpm':
#                    unit = v2_drpms.find_one({'_id' : ass_unit['unit_id']})

    return True

def _symlink_rpms(src_path, tgt_path, report):
    print "loading symlink_rpms src %s ; tgt %s" % (src_path, tgt_path)
    if not os.path.exists(src_path):
        # missing source path, skip migrate
        report.warning("Package %s does not exist" % src_path)
        return False
    distributor_working_dir = os.path.dirname(tgt_path)
    if not os.path.isdir(distributor_working_dir):
        os.makedirs(distributor_working_dir)
    print src_path, tgt_path
    if os.path.islink(tgt_path):
       os.unlink(tgt_path)
    os.symlink(src_path, tgt_path)
    print "Symlink created from %s -> %s" % (tgt_path, src_path)
    return True

def _symlink_distribution_files(unit, symlink_dir, report):
    source_path_dir  = unit['_storage_path']
    distro_files =  unit['files']
    src_treeinfo_path = None
    for treeinfo in ['treeinfo', '.treeinfo']:
        src_treeinfo_path = os.path.join(source_path_dir, treeinfo)
        if os.path.exists(src_treeinfo_path):
            # we found the treeinfo file
            break
    if src_treeinfo_path is not None:
        # create a symlink from content location to repo location.
        symlink_treeinfo_path = os.path.join(symlink_dir, treeinfo)
        print("creating treeinfo symlink from %s to %s" % (src_treeinfo_path, symlink_treeinfo_path))
        os.symlink(src_treeinfo_path, symlink_treeinfo_path)
    for dfile in distro_files:
        source_path = os.path.join(source_path_dir, dfile['relativepath'])
        symlink_path = os.path.join(symlink_dir, dfile['relativepath'])
        if os.path.exists(symlink_path):
            continue
        if not os.path.exists(source_path):
            report.error("Source path: %s is missing" % source_path)
            continue
        try:
            os.symlink(source_path, symlink_path)
        except Exception, e:
            report.error(str(e))
            continue
