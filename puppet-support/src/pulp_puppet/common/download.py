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


class StoredDownloadedContent(object):
    """
    Stores content on disk as it is retrieved by PyCurl. This currently does
    not support resuming a download and will need to be revisited to add
    that support.
    """
    def __init__(self, filename):
        self.filename = filename

        self.offset = 0
        self.file = None

    def open(self):
        """
        Sets the content object to be able to accept and store data sent to
        its update method.
        """
        self.file = open(self.filename, 'a+')

    def update(self, buffer):
        """
        Callback passed to PyCurl to use to write content as it is read.
        """
        self.file.seek(self.offset)
        self.file.write(buffer)
        self.offset += len(buffer)

    def close(self):
        """
        Closes the underlying file backing this content unit.
        """
        self.file.close()

    def delete(self):
        """
        Deletes the stored file.
        """
        if os.path.exists(self.filename):
            os.remove(self.filename)
