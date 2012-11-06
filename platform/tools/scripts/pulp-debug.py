#!/usr/bin/python
#
# Copyright (c) 2012 Red Hat, Inc.
#
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.
#
# Sayli Karmarkar <skarmark@redhat.com>

import os
import sys
import shutil
from datetime import datetime

from optparse import OptionParser

# List of relevant directories and files to collect information about Pulp configuration and logs

# Contents of these files, directories and output of commands will be copied when Pulp is installed

PULP_DIRS =  [ "/etc/pulp/",
               "/etc/gofer/plugins/",
               "/var/log/pulp/",
               "/etc/pulp/agent/",
             ]
               
PULP_FILES = [ "/etc/httpd/conf.d/pulp.conf",
               "/etc/yum/pluginconf.d/pulp-profile-update.conf",
               "/etc/pulp/repo_auth.conf",
               "/etc/pki/pulp/content/pulp-protected-repos",
               "/var/log/gofer/agent.log",
             ] 

PULP_COMMANDS = { "ls -lR /var/lib/pulp": {"filename" : "ls_-lR_var.lib.pulp",
                                           "access_path" : "/var/lib/pulp"} }

#-----------------------------------------------------------------------------------------------------

# Contents of these files, directories and output of commands will be copied when pulp-cds is installled

CDS_DIRS =  [ "/etc/pulp/",
              "/etc/gofer/plugins/",
              "/var/log/pulp-cds/",
            ]

CDS_FILES = [ "/etc/httpd/conf.d/pulp-cds.conf",
              "/var/log/gofer/agent.log",
            ]

CDS_COMMANDS = { "ls -lR /var/lib/pulp-cds": {"filename" : "ls_-lR_var.lib.pulp-cds",
                                              "access_path" : "/var/lib/pulp-cds"} }

#-----------------------------------------------------------------------------------------------------

def __parser():
    parser = OptionParser()
    parser.add_option(
        '--dir',
        dest='dir',
        help='Directory to place the tree containing debugging information; defaults to /tmp',
        default='/tmp')
    parser.add_option(
        '--name',
        dest='name',
        help='Given name is used for the base Directory containing debugging information; defaults to pulp-debug-(current_time in %Y-%m-%d-T%H-%M-%S format)')
    parser.add_option(
        '--cds',
        action="store_true",
        dest="cds",
        default=False,
        help="If the script needs to be executed to collect CDS information instead of RHUA")
    return parser

# Checks whether user has root access to run this script
def check_root():
    if not os.geteuid() == 0:
        sys.exit("You need to have root access to run this script")

# If directory exists, copies contents of each directory into base directory
def copy_dirs(dirs, base_dir):
#    print ""
    for dir in dirs:
        if not os.path.exists(dir):
            continue
        dst = os.path.join(base_dir, dir.lstrip('/'))
        try:
            print "Copying contents of directory [%s] to [%s] " % (dir, dst) 
            shutil.copytree(dir, dst, symlinks=False)
        except:
            # Ignore error raised by shutil when a sub-directory already exists
            pass
        
# If file exists, copies the file into base directory
def copy_files(files, base_dir):
#    print ""
    for file in files:
        if not os.path.exists(file):
            continue
        path, filename = os.path.split(file)
        path = os.path.join(base_dir, path.lstrip('/'))
        if not os.path.exists(path):
            os.makedirs(path)
        print "Copying file [%s] to [%s]" % (file, path)
        shutil.copy(file, path)
        
# Runs given commands and copies output under commands directory into the base directory
def run_commands(commands, base_dir):
#    print ""
    commands_dir = os.path.join(base_dir, 'commands')
    if not os.path.exists(commands_dir):
        print "Creating commands directory [%s]" % commands_dir
        os.mkdir(commands_dir)

    for command, command_info in commands.items():
        if os.access(command_info['access_path'], os.R_OK):
            location = os.path.join(commands_dir, command_info['filename'])
            print "Storing output of command [%s] in [%s]" % (commands_dir, location)
            os.system(command + ' >> ' + location)
        

if __name__=="__main__":
    
    # Get the location to store debugging content
    parser = __parser()
    (opt, args) = parser.parse_args()
    
    if not os.path.exists(opt.dir):
        sys.exit('Directory [%s] does not exists' % opt.dir)
    
    # Make sure user has root access to run this script
    check_root()
    
    # Create a base directory to store debugging information
    if opt.name:
        dir_name = opt.name
    else:
        now = datetime.now().strftime("%Y-%m-%d-T%H-%M-%S")
        dir_name = 'pulp-debug-' + now
 
    base_dir = os.path.join(opt.dir, dir_name)

    if os.path.exists(base_dir):
        sys.exit("Directory with path [%s] already exists; please delete and re-run the script" % dir_name)
    else:
        os.makedirs(base_dir)
        print("\nSuccessfully created directory [%s]\n" % base_dir)
        
    if opt.cds:
        # Collect CDS specific debugging information
        copy_dirs(CDS_DIRS, base_dir)
        copy_files(CDS_FILES, base_dir)
        run_commands(CDS_COMMANDS, base_dir)
    else:
        # Collect Pulp specific debugging information
        copy_dirs(PULP_DIRS, base_dir)
        print ""
        copy_files(PULP_FILES, base_dir)
        print ""
        run_commands(PULP_COMMANDS, base_dir)
        print ""

