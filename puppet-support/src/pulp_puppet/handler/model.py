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

import pickle
import os

from pulp_puppet.common import constants


class BoundRepositoryFile(object):

    def __init__(self, config, repo_id):
        super(BoundRepositoryFile, self).__init__()
        self.config = config

        # Repository Metadata
        self.repo_id = repo_id
        self.protocol = None
        self.host = None

    # -- state ----------------------------------------------------------------

    @property
    def repo_url(self):
        url = '/'.join([constants.WEB_ALIAS, self.repo_id])
        return url

    @property
    def filename(self):
        return self._filename(self.repo_id, self.config)

    def update_from_binding(self, details):
        self.protocol = details[constants.PAYLOAD_PROTOCOL]
        self.host = details[constants.PAYLOAD_SERVER]

    # -- lifecycle ------------------------------------------------------------

    @classmethod
    def load(cls, filename):
        """

        :param cls:
        :param filename:
        :return:
        :rtype:  BoundRepositoryFile
        """
        f = open(filename, 'r')
        unpickled = pickle.load(f)
        f.close()

        return unpickled

    def save(self):
        # If there's already a definition, replace it
        self.delete()

        f = open(self.filename, 'w')
        pickle.dump(self, f)
        f.close()

    def delete(self):
        if os.path.exists(self.filename):
            os.remove(self.filename)

    # -- private --------------------------------------------------------------

    @staticmethod
    def _filename(repo_id, config):
        repo_dir = config[constants.CONFIG_CONSUMER_REPO_DIR]
        filename = os.path.join(repo_dir, repo_id)
        return filename
