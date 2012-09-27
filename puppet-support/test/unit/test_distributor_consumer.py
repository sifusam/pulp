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

from ConfigParser import SafeConfigParser
import unittest

from pulp.plugins.config import PluginCallConfiguration
from pulp.plugins.model import Repository

from pulp_puppet.common import constants
from pulp_puppet.distributor import consumer


class ConsumerPayloadTests(unittest.TestCase):

    def setUp(self):
        super(ConsumerPayloadTests, self).setUp()

        self.server_config = SafeConfigParser()
        self.server_config.add_section('server')
        self.server_config.set('server', 'server_name', value='pulp-server')

        self.repo_plugin_config = {
            constants.CONFIG_SERVE_HTTP : True,
            constants.CONFIG_SERVE_HTTPS : True,
        }

        self.call_config = PluginCallConfiguration(self.server_config, {},
                                                   self.repo_plugin_config)

        self.repo = Repository('fake-repo')

    def test_create_consumer_payload(self):
        # Test
        payload = consumer.create_consumer_payload(self.repo, self.call_config)

        # Verify
        self.assertEqual(payload[constants.PAYLOAD_PROTOCOL], constants.PROTOCOL_HTTPS)
        self.assertEqual(payload[constants.PAYLOAD_SERVER], 'pulp-server')

    def test_create_consumer_payload_http(self):
        # Test
        self.repo_plugin_config[constants.CONFIG_SERVE_HTTPS] = False
        payload = consumer.create_consumer_payload(self.repo, self.call_config)

        # Verify
        self.assertEqual(payload[constants.PAYLOAD_PROTOCOL], constants.PROTOCOL_HTTP)
        self.assertEqual(payload[constants.PAYLOAD_SERVER], 'pulp-server')
