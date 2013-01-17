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

import os
import sys
import tempfile
import shutil
import time
import re
from mock import Mock, patch
from base import WebTest

sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/mocks")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../../platform/src/")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../plugins/importers/citrus_importer")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../plugins/distributors/citrus_distributor")
sys.path.insert(0, os.path.abspath(os.path.dirname(__file__)) + "/../../handlers")

from distributor import CitrusDistributor
from importer import CitrusImporter
from citrus import RepositoryHandler

from pulp.plugins.loader import api as plugin_api
from pulp.plugins.types import database as unit_db
from pulp.server.db.model.repository import Repo, RepoDistributor, RepoImporter
from pulp.server.db.model.repository import RepoContentUnit
from pulp.server.db.model.consumer import Consumer, Bind
from pulp.plugins.conduits.repo_publish import RepoPublishConduit
from pulp.plugins.conduits.repo_sync import RepoSyncConduit
from pulp.server.managers import factory as managers
from pulp.bindings.bindings import Bindings
from pulp.bindings.server import PulpConnection
from pulp.server.config import config as pulp_conf
from pulp.agent.lib.conduit import Conduit

CITRUS_IMPORTER = 'citrus_importer'
CITRUS_DISTRUBUTOR = 'citrus_distributor'

class Repository(object):

    def __init__(self, id):
        self.id = id


class PluginTestBase(WebTest):

    REPO_ID = 'test-repo'
    UNIT_TYPE_ID = 'rpm'
    UNIT_ID = 'test_unit_%d'
    UNIT_METADATA = {'A':'a','B':'b', 'N': 0}
    TYPEDEF_ID = UNIT_TYPE_ID
    NUM_UNITS = 3

    @classmethod
    def tmpdir(cls, role):
        dir = tempfile.mkdtemp(dir=cls.TMP_ROOT, prefix=role)
        return dir

    def setUp(self):
        WebTest.setUp(self)
        self.upfs = self.tmpdir('upstream-')
        self.downfs = self.tmpdir('downstream-')
        Consumer.get_collection().remove()
        Bind.get_collection().remove()
        Repo.get_collection().remove()
        RepoDistributor.get_collection().remove()
        RepoImporter.get_collection().remove()
        RepoContentUnit.get_collection().remove()
        unit_db.clean()
        plugin_api._create_manager()
        plugin_api._MANAGER.importers.add_plugin(CITRUS_IMPORTER, CitrusImporter, {})
        plugin_api._MANAGER.distributors.add_plugin(CITRUS_DISTRUBUTOR, CitrusDistributor, {})
        unit_db.type_definition = \
            Mock(return_value=dict(id=self.TYPEDEF_ID, unit_key=self.UNIT_METADATA))
        unit_db.type_units_unit_key = \
            Mock(return_value=['A', 'B', 'N'])

    def tearDown(self):
        WebTest.tearDown(self)
        shutil.rmtree(self.upfs)
        shutil.rmtree(self.downfs)
        Consumer.get_collection().remove()
        Bind.get_collection().remove()
        Repo.get_collection().remove()
        RepoDistributor.get_collection().remove()
        RepoImporter.get_collection().remove()
        RepoContentUnit.get_collection().remove()
        unit_db.clean()

    def populate(self):
        # make content/ dir.
        os.makedirs(os.path.join(self.upfs, 'content'))
        pulp_conf.set('server', 'storage_dir', self.upfs)
        # create repo
        manager = managers.repo_manager()
        manager.create_repo(self.REPO_ID)
        manager = managers.repo_distributor_manager()
        # add distrubutor
        manager.add_distributor(
            self.REPO_ID,
            CITRUS_DISTRUBUTOR,
            {},
            False,
            distributor_id=CITRUS_DISTRUBUTOR)
        # add units
        for n in range(0, self.NUM_UNITS):
            unit_id = self.UNIT_ID % n
            unit = dict(self.UNIT_METADATA)
            unit['N'] = n
            # add unit file
            storage_dir = pulp_conf.get('server', 'storage_dir')
            storage_path = \
                os.path.join(storage_dir, 'content',
                    '.'.join((unit_id, self.UNIT_TYPE_ID)))
            unit['_storage_path'] = storage_path
            fp = open(storage_path, 'w+')
            fp.write(unit_id)
            fp.close()
            # add unit
            manager = managers.content_manager()
            manager.add_content_unit(
                self.UNIT_TYPE_ID,
                unit_id,
                unit)
            manager = managers.repo_unit_association_manager()
            # associate unit
            manager.associate_unit_by_id(
                self.REPO_ID,
                self.UNIT_TYPE_ID,
                unit_id,
                RepoContentUnit.OWNER_TYPE_IMPORTER,
                CITRUS_IMPORTER)


class TestDistributor(PluginTestBase):

    def test_payload(self):
        # Setup
        self.populate()
        pulp_conf.set('server', 'storage_dir', self.upfs)
        # Test
        dist = CitrusDistributor()
        repo = Repository(self.REPO_ID)
        payload = dist.create_consumer_payload(repo, {})
        # Verify
        print payload

    def test_publish(self):
        # Setup
        self.populate()
        pulp_conf.set('server', 'storage_dir', self.upfs)
        # Test
        dist = CitrusDistributor()
        repo = Repository(self.REPO_ID)
        cfg = dict(virtual_host=(self.upfs, self.upfs))
        conduit = RepoPublishConduit(self.REPO_ID, CITRUS_DISTRUBUTOR)
        dist.publish_repo(repo, conduit, cfg)
        # Verify
        # TODO: verify published


class ImporterTest(PluginTestBase):

    def test_import(self):
        # Setup
        self.populate()
        pulp_conf.set('server', 'storage_dir', self.upfs)
        dist = CitrusDistributor()
        repo = Repository(self.REPO_ID)
        cfg = dict(virtual_host=(self.upfs, self.upfs))
        conduit = RepoPublishConduit(self.REPO_ID, CITRUS_DISTRUBUTOR)
        dist.publish_repo(repo, conduit, cfg)
        Repo.get_collection().remove()
        RepoDistributor.get_collection().remove()
        RepoContentUnit.get_collection().remove()
        unit_db.clean()
        # Test
        importer = CitrusImporter()
        cfg = dict(
            manifest_url=dist.publisher(repo, cfg).manifest_path())
        conduit = RepoSyncConduit(
            self.REPO_ID,
            CITRUS_IMPORTER,
            RepoContentUnit.OWNER_TYPE_IMPORTER,
            CITRUS_IMPORTER)
        importer.sync_repo(repo, conduit, cfg)
        # Verify
        units = conduit.get_units()
        self.assertEquals(len(units), self.NUM_UNITS)


class TestHandler(RepositoryHandler):

    def __init__(self, tester, cfg={}):
        self.tester = tester
        RepositoryHandler.__init__(self, cfg)

    def synchronize(self, progress, binds, options):
        self.tester.clean()
        return RepositoryHandler.synchronize(self, progress, binds, options)


class TestAgentPlugin(PluginTestBase):

    PULP_ID = 'downstream'

    def populate(self):
        PluginTestBase.populate(self)
        self.virtual_host = (self.upfs, self.upfs)
        # register downstream
        manager = managers.consumer_manager()
        manager.register(self.PULP_ID)
        manager = managers.repo_importer_manager()
        # add importer
        cfg = dict(manifest_url='http://apple.com')
        manager.set_importer(self.REPO_ID, CITRUS_IMPORTER, cfg)
        # add distrubutor
        manager = managers.repo_distributor_manager()
        cfg = dict(base_url='file://', virtual_host=self.virtual_host)
        manager.add_distributor(
            self.REPO_ID,
            CITRUS_DISTRUBUTOR,
            cfg,
            False,
            CITRUS_DISTRUBUTOR)
        # bind
        manager = managers.consumer_bind_manager()
        manager.bind(self.PULP_ID, self.REPO_ID, CITRUS_DISTRUBUTOR)

    def clean(self):
        Bind.get_collection().remove()
        Repo.get_collection().remove()
        RepoDistributor.get_collection().remove()
        RepoImporter.get_collection().remove()
        RepoContentUnit.get_collection().remove()
        unit_db.clean()

    def verify(self, num_units=PluginTestBase.NUM_UNITS):
        # repository
        manager = managers.repo_query_manager()
        manager.get_repository(self.REPO_ID)
        # importer
        manager = managers.repo_importer_manager()
        importer = manager.get_importer(self.REPO_ID)
        manifest_url = importer['config']['manifest_url']
        self.assertTrue(manifest_url.endswith('%s/units.json' % self.REPO_ID))
        # distributor
        manager = managers.repo_distributor_manager()
        distributor = manager.get_distributor(self.REPO_ID, CITRUS_DISTRUBUTOR)
        base_url = distributor['config']['base_url']
        self.assertEqual(base_url, 'file://')
        virtual_host = distributor['config']['virtual_host']
        self.assertEqual(virtual_host[0], self.upfs)
        self.assertEqual(virtual_host[1], self.upfs)
        # check units
        manager = managers.repo_unit_association_query_manager()
        units = manager.get_units(self.REPO_ID)
        units = dict([(u['metadata']['N'], u) for u in units])
        self.assertEqual(len(units), num_units)
        for n in range(0, num_units):
            unit = units[n]
            unit_id = self.UNIT_ID % n
            metadata = unit['metadata']
            storage_path = metadata['_storage_path'].replace('//', '/')
            self.assertEqual(unit['unit_type_id'], self.UNIT_TYPE_ID)
            self.assertEqual(unit['repo_id'], self.REPO_ID)
            self.assertEqual(unit['owner_id'], CITRUS_IMPORTER)
            file = '.'.join((unit_id, self.UNIT_TYPE_ID))
            self.assertEqual(storage_path, os.path.join(self.downfs, 'content', file))
            self.assertTrue(os.path.exists(storage_path))
            # unit files
        files = os.listdir(os.path.join(self.downfs, 'content'))
        self.assertEqual(num_units, len(files))

    @patch('citrus.Bundle.cn', return_value=PULP_ID)
    def test_handler(self, unused):
        """
        Test the end-to-end collaboration of:
          distributor(publish)->handler(update)->importer(sync)
        This produces a file structure of:
          storage    - The upstream unit storage.
          upstream   - The upstream publishing location
          downstream - The downstream unit storage
        For example:

            citrus/
            ├── downstream-2BUtUa
            │   ├── content
            │   │   └── test_unit.rpm
            │   └── working
            │       └── repos
            │           └── test-repo
            │               ├── distributors
            │               │   └── citrus_distributor
            │               └── importers
            │                   └── citrus_importer
            ├── storage
            └── upstream-SgASM7
                ├── content
                │   └── test_unit.rpm
                ├── test-repo
                │   ├── content
                │   │   └── 3ae69ea97c -> /tmp/pulp/citrus/upstream-SgASM7/content/test_unit.rpm
                │   └── units.json
                └── working
                    └── repos
                        └── test-repo
                            ├── distributors
                            │   └── citrus_distributor
                            └── importers
                                └── citrus_importer

        @param unused:
        @return:
        """
        _report = []
        conn = PulpConnection(None, server_wrapper=self)
        binding = Bindings(conn)
        @patch('citrus.Local.binding', binding)
        @patch('citrus.Remote.binding', binding)
        def test_handler(*unused):
            # publish
            self.populate()
            pulp_conf.set('server', 'storage_dir', self.upfs)
            dist = CitrusDistributor()
            repo = Repository(self.REPO_ID)
            cfg = dict(base_url='file://', virtual_host=self.virtual_host)
            conduit = RepoPublishConduit(self.REPO_ID, CITRUS_DISTRUBUTOR)
            dist.publish_repo(repo, conduit, cfg)
            units = []
            options = dict(all=True)
            handler = TestHandler(self)
            pulp_conf.set('server', 'storage_dir', self.downfs)
            report = handler.update(Conduit(), units, options)
            _report.append(report)
        test_handler()
        time.sleep(2)
        # Verify
        report = _report[0]
        self.assertTrue(report.succeeded)
        merge = report.details['merge']
        self.assertEqual(merge['added'], [self.REPO_ID])
        self.assertEqual(merge['merged'], [])
        self.assertEqual(merge['removed'], [])
        synchronization = report.details['synchronization'][self.REPO_ID]
        self.assertEqual(synchronization['added_count'], self.NUM_UNITS)
        self.assertEqual(synchronization['removed_count'], 0)
        details = synchronization['details']
        self.assertEqual(len(details['added']), self.NUM_UNITS)
        self.assertEqual(len(details['removed']), 0)
        self.assertEqual(len(details['errors']), 0)
        self.verify()

    def clean_units(self):
        RepoContentUnit.get_collection().remove()
        unit_db.clean()

    @patch('citrus.Bundle.cn', return_value=PULP_ID)
    def test_handler_merge(self, unused):
        """
        Test the end-to-end collaboration of:
          distributor(publish)->handler(update)->importer(sync)
        This test does NOT clean so citrus will merge.
        @see: test_handler for directory tree details.
        @param unused:
        @return:
        """
        _report = []
        self.clean = self.clean_units
        conn = PulpConnection(None, server_wrapper=self)
        binding = Bindings(conn)
        @patch('citrus.Local.binding', binding)
        @patch('citrus.Remote.binding', binding)
        def test_handler(*unused):
            # publish
            self.populate()
            pulp_conf.set('server', 'storage_dir', self.upfs)
            dist = CitrusDistributor()
            repo = Repository(self.REPO_ID)
            cfg = dict(base_url='file://', virtual_host=self.virtual_host)
            conduit = RepoPublishConduit(self.REPO_ID, CITRUS_DISTRUBUTOR)
            dist.publish_repo(repo, conduit, cfg)
            units = []
            options = dict(all=True)
            handler = TestHandler(self)
            pulp_conf.set('server', 'storage_dir', self.downfs)
            report = handler.update(Conduit(), units, options)
            _report.append(report)
        test_handler()
        time.sleep(2)
        # Verify
        report = _report[0]
        self.assertTrue(report.succeeded)
        merge = report.details['merge']
        self.assertEqual(merge['added'], [])
        self.assertEqual(merge['merged'], [self.REPO_ID])
        self.assertEqual(merge['removed'], [])
        synchronization = report.details['synchronization'][self.REPO_ID]
        self.assertTrue(synchronization['succeeded'])
        importer_report = synchronization['report']
        self.assertEqual(importer_report['added_count'], self.NUM_UNITS)
        self.assertEqual(importer_report['removed_count'], 0)
        details = importer_report['details']
        self.assertEqual(len(details['added']), self.NUM_UNITS)
        self.assertEqual(len(details['removed']), 0)
        self.assertEqual(len(details['errors']), 0)
        self.verify()

    @patch('citrus.Bundle.cn', return_value=PULP_ID)
    @patch('pulp.citrus.http.transport.HttpTransport._download', side_effect=Exception('No Route To Host'))
    def test_handler_unit_errors(self, *unused):
        """
        Test the end-to-end collaboration of:
          distributor(publish)->handler(update)->importer(sync)
        @see: test_handler for directory tree details.
        @param unused:
        @return:
        """
        _report = []
        conn = PulpConnection(None, server_wrapper=self)
        binding = Bindings(conn)
        @patch('citrus.Local.binding', binding)
        @patch('citrus.Remote.binding', binding)
        def test_handler(*unused):
            # publish
            self.populate()
            pulp_conf.set('server', 'storage_dir', self.upfs)
            dist = CitrusDistributor()
            repo = Repository(self.REPO_ID)
            cfg = dict(base_url='file://', virtual_host=self.virtual_host)
            conduit = RepoPublishConduit(self.REPO_ID, CITRUS_DISTRUBUTOR)
            dist.publish_repo(repo, conduit, cfg)
            units = []
            options = dict(all=True)
            handler = TestHandler(self)
            pulp_conf.set('server', 'storage_dir', self.downfs)
            os.makedirs(os.path.join(self.downfs, 'content'))
            report = handler.update(Conduit(), units, options)
            _report.append(report)
        test_handler()
        time.sleep(2)
        # Verify
        report = _report[0]
        self.assertTrue(report.succeeded)
        merge = report.details['merge']
        self.assertEqual(merge['added'], [self.REPO_ID])
        self.assertEqual(merge['merged'], [])
        self.assertEqual(merge['removed'], [])
        synchronization = report.details['synchronization'][self.REPO_ID]
        self.assertTrue(synchronization['succeeded'])
        importer_report = synchronization['report']
        self.assertEqual(importer_report['added_count'], 0)
        self.assertEqual(importer_report['removed_count'], 0)
        details = importer_report['details']
        self.assertEqual(len(details['added']), 0)
        self.assertEqual(len(details['removed']), 0)
        self.assertEqual(len(details['errors']), self.NUM_UNITS)
        self.verify(0)

    @patch('citrus.Bundle.cn', return_value=PULP_ID)
    @patch('pulp.citrus.http.transport.HttpTransport.download', side_effect=Exception('Barf'))
    def test_handler_transport_exception(self, *unused):
        """
        Test the end-to-end collaboration of:
          distributor(publish)->handler(update)->importer(sync)
        @see: test_handler for directory tree details.
        @param unused:
        @return:
        """
        _report = []
        conn = PulpConnection(None, server_wrapper=self)
        binding = Bindings(conn)
        @patch('citrus.Local.binding', binding)
        @patch('citrus.Remote.binding', binding)
        def test_handler(*unused):
            # publish
            self.populate()
            pulp_conf.set('server', 'storage_dir', self.upfs)
            dist = CitrusDistributor()
            repo = Repository(self.REPO_ID)
            cfg = dict(base_url='file://', virtual_host=self.virtual_host)
            conduit = RepoPublishConduit(self.REPO_ID, CITRUS_DISTRUBUTOR)
            dist.publish_repo(repo, conduit, cfg)
            units = []
            options = dict(all=True)
            handler = TestHandler(self)
            pulp_conf.set('server', 'storage_dir', self.downfs)
            os.makedirs(os.path.join(self.downfs, 'content'))
            report = handler.update(Conduit(), units, options)
            _report.append(report)
        test_handler()
        time.sleep(2)
        # Verify
        report = _report[0]
        self.assertTrue(report.succeeded)
        errors = report.details['errors']
        self.assertEqual(len(errors), 3)
        merge = report.details['merge']
        self.assertEqual(merge['added'], [self.REPO_ID])
        self.assertEqual(merge['merged'], [])
        self.assertEqual(merge['removed'], [])
        synchronization = report.details['synchronization'][self.REPO_ID]
        self.assertFalse(synchronization['succeeded'])
        exception = synchronization['exception']
        self.assertTrue(len(exception) > 0)
        self.verify(0)