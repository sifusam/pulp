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

from pulp_puppet.common import constants


def create_consumer_payload(repo, config):
    """
    Generates the details a puppet master will need to access the given
    repository.

    :param repo: repository being accessed
    :type  repo: pulp.plugins.model.Repository
    :param config: call configuration passed to the plugin
    :type  config: pulp.plugins.config.PluginCallConfiguration
    :return: payload to send to the puppet master
    :rtype:  dict
    """

    payload = {}

    # The consumer needs to know which protocol to use, so figure out which
    # it's exposed under, giving preference to SSL first, and indicate it.
    if config.get(constants.CONFIG_SERVE_HTTPS, None):
        protocol = constants.PROTOCOL_HTTPS
    else:
        protocol = constants.PROTOCOL_HTTP

    payload[constants.PAYLOAD_PROTOCOL] = protocol

    # Stuff in the hostname of the server
    payload[constants.PAYLOAD_SERVER] = config.get_server_config().get('server', 'server_name')

    return payload

