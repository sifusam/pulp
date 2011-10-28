# -*- coding: utf-8 -*-
#
# Copyright © 2011 Red Hat, Inc.
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
Provides a loosely coupled way of retrieving references into other manager
instances. Test cases can manipulate this module to mock out the class of
manager returned for a given type to isolate and simulate edge cases such
as exceptions.

When changing manager class mappings for a test, be sure to call reset()
in the test clean up to restore the mappings to the defaults. Failing to
do so may indirectly break other tests.
"""


# -- constants ----------------------------------------------------------------

# Keys used to look up a specific builtin manager (please alphabetize)
TYPE_CDS              = 'cds-manager'
TYPE_CONTENT          = 'content-manager'
TYPE_CONTENT_QUERY    = 'content-query-manager'
TYPE_CONTENT_UPLOAD   = 'content-upload-manager'
TYPE_PLUGIN_MANAGER   = 'plugin-manager'
TYPE_REPO             = 'repo-manager'
TYPE_REPO_ASSOCIATION = 'repo-association-manager'
TYPE_REPO_CLONE       = 'repo-clone-manager'
TYPE_REPO_PUBLISH     = 'repo-publish-manager'
TYPE_REPO_QUERY       = 'repo-query-manager'
TYPE_REPO_SYNC        = 'repo-sync-manager'

# Mapping of key to class that will be instantiated in the factory method
# Initialized to a copy of the defaults so changes won't break the defaults
_CLASSES = {}

# -- exceptions ---------------------------------------------------------------

class InvalidType(Exception):
    """
    Raised when a manager type is requested that has no class mapping.
    """

    def __init__(self, type_key):
        Exception.__init__(self)
        self.type_key = type_key

    def __str__(self):
        return 'Invalid manager type requested [%s]' % self.type_key

# -- manager retrieval --------------------------------------------------------

# When adding these syntactic sugar methods, please use the @rtype tag to make
# sure IDEs can correctly guess at the returned type and provide auto-complete.

# Be sure to add an entry to test_syntactic_sugar_methods in test_manager_factory.py
# to verify the correct type of manager is returned.

def repo_manager():
    """
    @rtype: L{pulp.server.managers.repo.cud.RepoManager}
    """
    return get_manager(TYPE_REPO)

def repo_unit_association_manager():
    """
    @rtype: L{pulp.server.managers.repo.unit_association.RepoUnitAssociationManager}
    """
    return get_manager(TYPE_REPO_ASSOCIATION)

def repo_clone_manager():
    """
    @rtype: L{pulp.server.managers.repo.clone.RepoCloneManager}
    """
    return get_manager(TYPE_REPO_CLONE)

def repo_publish_manager():
    """
    @rtype: L{pulp.server.managers.repo.publish.RepoPublishManager}
    """
    return get_manager(TYPE_REPO_PUBLISH)

def repo_query_manager():
    """
    @rtype: L{pulp.server.managers.repo.query.RepoQueryManager}
    """
    return get_manager(TYPE_REPO_QUERY)

def repo_sync_manager():
    """
    @rtype: L{pulp.server.managers.repo.sync.RepoSyncManager}
    """
    return get_manager(TYPE_REPO_SYNC)

def content_manager():
    """
    @rtype: L{pulp.server.managers.content.cud.ContentManager}
    """
    return get_manager(TYPE_CONTENT)

def content_query_manager():
    """
    @rtype: L{pulp.server.managers.content.query.ContentQueryManager}
    """
    return get_manager(TYPE_CONTENT_QUERY)

def content_upload_manager():
    """
    @rtype: L{pulp.server.managers.content.upload.ContentUploadManager}
    """
    return get_manager(TYPE_CONTENT_UPLOAD)

def plugin_manager():
    """
    @rtype: L{pulp.server.managers.plugin.PluginManager}
    """
    return get_manager(TYPE_PLUGIN_MANAGER)
    
# -- other --------------------------------------------------------------------

def initialize():
    """
    Initialize the manager factory by importing and setting Pulp's builtin
    (read: default) managers.
    """
    # imports for individual managers to prevent circular imports
    from pulp.server.managers.content.cud import ContentManager
    from pulp.server.managers.content.query import ContentQueryManager
    from pulp.server.managers.content.upload import ContentUploadManager
    from pulp.server.managers.plugin import PluginManager
    from pulp.server.managers.repo.cud import RepoManager
    from pulp.server.managers.repo.unit_association import RepoUnitAssociationManager
    from pulp.server.managers.repo.clone import RepoCloneManager
    from pulp.server.managers.repo.publish import RepoPublishManager
    from pulp.server.managers.repo.query import RepoQueryManager
    from pulp.server.managers.repo.sync import RepoSyncManager
    # Builtins for a normal running Pulp server (used to reset the state of the
    # factory between runs)
    builtins = {
        TYPE_CONTENT: ContentManager,
        TYPE_CONTENT_QUERY: ContentQueryManager,
        TYPE_CONTENT_UPLOAD: ContentUploadManager,
        TYPE_PLUGIN_MANAGER: PluginManager,
        TYPE_REPO: RepoManager,
        TYPE_REPO_ASSOCIATION: RepoUnitAssociationManager,
        TYPE_REPO_CLONE: RepoCloneManager,
        TYPE_REPO_PUBLISH: RepoPublishManager,
        TYPE_REPO_QUERY: RepoQueryManager,
        TYPE_REPO_SYNC: RepoSyncManager,
    }
    _CLASSES.update(builtins)

def get_manager(type_key):
    """
    Returns a manager instance of the given type according to the current
    manager class mappings.

    This can be called directly, but the preferred method for retrieving managers
    is to use the syntactic sugar methods in this module.

    @param type_key: identifies the manager being requested; should be one of
                     the TYPE_* constants in this module
    @type  type_key: str

    @return: manager instance that (should) adhere to the expected API for
             managers of the requested type
    @rtype:  some sort of object  :)

    @raises InvalidType: if there is no class mapping for the requested type
    """

    if type_key not in _CLASSES:
        raise InvalidType(type_key)

    cls = _CLASSES[type_key]
    manager = cls()

    return manager

def register_manager(type_key, manager_class):
    """
    Sets the manager class for the given type key, either replacing the existing
    mapping or creating a new one.

    @param type_key: identifies the manager type
    @type  type_key: str

    @param manager_class: class to instantiate when requesting a manager of the
                          type specified in type_key
    @type  manager_class: class
    """

    _CLASSES[type_key] = manager_class

def reset():
    """
    Resets the type to class mappings back to the defaults. This should be called
    in test cleanup to prepare the state for other test runs.
    """

    global _CLASSES
    _CLASSES = {}
    initialize()