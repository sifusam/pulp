# -*- coding: utf-8 -*-
#
# Copyright © 2012 Red Hat, Inc.
#
# This software is licensed to you under the GNU General Public
# License as published by the Free Software Foundation; either version
# 2 of the License (GPLv2) or (at your option) any later version.
# There is NO WARRANTY for this software, express or implied,
# including the implied warranties of MERCHANTABILITY,
# NON-INFRINGEMENT, or FITNESS FOR A PARTICULAR PURPOSE. You should
# have received a copy of GPLv2 along with this software; if not, see
# http://www.gnu.org/licenses/old-licenses/gpl-2.0.txt.

import copy

from pulp.common.tags import action_tag, resource_tag

from pulp.server import config as pulp_config
from pulp.server import exceptions as pulp_exceptions
from pulp.server.dispatch import constants as dispatch_constants
from pulp.server.dispatch import factory as dispatch_factory
from pulp.server.dispatch.call import CallRequest
from pulp.server.managers import factory as managers_factory
from pulp.server.managers.schedule import utils as schedule_utils


<<<<<<< HEAD
=======
UNIT_INSTALL_ACTION = 'unit_install'
UNIT_UPDATE_ACTION = 'unit_update'
UNIT_UNINSTALL_ACTION = 'unit_uninstall'
>>>>>>> jconnor-scheduled-content
_UNIT_OPTION_KEYS = ('options',)


class ConsumerScheduleManager(object):
<<<<<<< HEAD

    @staticmethod
    def _validate_consumer(consumer_id):
        consumer_manager = managers_factory.consumer_manager()
        consumer_manager.get_consumer(consumer_id)

# consumer content install schedule manager ------------------------------------

class ConsumerContentInstallScheduleManager(ConsumerScheduleManager):
=======
    """
    Abstract base class for consumer content management schedules.
    """
>>>>>>> jconnor-scheduled-content

    @staticmethod
    def _validate_consumer(consumer_id):
        consumer_manager = managers_factory.consumer_manager()
        consumer_manager.get_consumer(consumer_id)

    def _create_schedule(self, management_method, management_action_name, consumer_id, units, options, schedule_data):
        self._validate_consumer(consumer_id)
<<<<<<< HEAD
        schedule_utils.validate_keys(install_options, _UNIT_OPTION_KEYS)
=======
        schedule_utils.validate_keys(options, _UNIT_OPTION_KEYS)
>>>>>>> jconnor-scheduled-content
        if 'schedule' not in schedule_data:
            raise pulp_exceptions.MissingValue(['schedule'])

        args = [consumer_id]
        kwargs = {'units': units,
                  'options': options.get('options', {})}
        weight = pulp_config.config.getint('tasks', 'consumer_content_weight')
        tags = [resource_tag(dispatch_constants.RESOURCE_CONSUMER_TYPE, consumer_id),
                action_tag(management_action_name),
                action_tag('scheduled_' + management_action_name)]
        call_request = CallRequest(management_method, args, kwargs, weight=weight, tags=tags, archive=True)
        call_request.reads_resource(dispatch_constants.RESOURCE_CONSUMER_TYPE, consumer_id)

        scheduler = dispatch_factory.scheduler()
        schedule_id = scheduler.add(call_request, **schedule_data)
        return schedule_id

    def _update_schedule(self, consumer_id, schedule_id, units=None, options=None, schedule_data=None):
        self._validate_consumer(consumer_id)
        schedule_updates = copy.copy(schedule_data) or {}

        scheduler = dispatch_factory.scheduler()
        report = scheduler.get(schedule_id)
        call_request = report['call_request']

        if units is not None:
            call_request.kwargs['units'] = units
            schedule_updates['call_request'] = call_request

        if options is not None and 'options' in options:
            call_request.kwargs['options'] = options['options']
            schedule_updates['call_request'] = call_request

        scheduler.update(schedule_id, **schedule_updates)

    def _delete_schedule(self, consumer_id, schedule_id):
        self._validate_consumer(consumer_id)

        scheduler = dispatch_factory.scheduler()
        scheduler.remove(schedule_id)

    def _delete_all_schedules(self, management_action_name, consumer_id):
        self._validate_consumer(consumer_id)

        scheduler = dispatch_factory.scheduler()
        consumer_tag = resource_tag(dispatch_constants.RESOURCE_CONSUMER_TYPE, consumer_id)
        management_tag = action_tag(management_action_name)
        reports = scheduler.find(consumer_tag, management_tag)

        for r in reports:
            scheduler.remove(r['call_report']['schedule_id'])

# consumer content install schedule manager ------------------------------------

class ConsumerContentInstallScheduleManager(ConsumerScheduleManager):

    def create_unit_install_schedule(self, consumer_id, units, install_options, schedule_data ):
        """
        Create a schedule for installing content units on a consumer.
        @param consumer_id: unique id for the consumer
        @param units: list of unit type and unit key dicts
        @param install_options: options to pass to the install manager
        @param schedule_data: scheduling data
        @return: schedule id
        """
        manager = managers_factory.consumer_agent_manager()
        return self._create_schedule(manager.install_content, UNIT_INSTALL_ACTION, consumer_id, units, install_options, schedule_data)

    def update_unit_install_schedule(self, consumer_id, schedule_id, units=None, install_options=None, schedule_data=None):
        """
        Update an existing schedule for installing content units on a consumer.
        @param consumer_id: unique id for the consumer
        @param schedule_id: unique id for the schedule
        @param units: optional list of units to install
        @param install_options: optional options to pass to the install manager
        @param schedule_data: optional schedule updates
        """
        return self._update_schedule(consumer_id, schedule_id, units, install_options, schedule_data)

    def delete_unit_install_schedule(self, consumer_id, schedule_id):
        """
        Delete an existing schedule for installing content units on a consumer.
        @param consumer_id: unique id of the consumer
        @param schedule_id: unique id of the schedule
        """
        return self._delete_schedule(consumer_id, schedule_id)

    def delete_all_unit_install_schedules(self, consumer_id):
        """
        Delete all unit install schedules for a consumer.
        Useful for unassociating consumers from the server.
        @param consumer_id: unique id of the consumer
        """
        return self._delete_all_schedules(UNIT_INSTALL_ACTION, consumer_id)

# consumer content update schedule manager -------------------------------------

class ConsumerContentUpdateScheduleManager(ConsumerScheduleManager):

<<<<<<< HEAD
# consumer content update schedule manager -------------------------------------

class ConsumerContentUpdateScheduleManager(ConsumerScheduleManager):

=======
>>>>>>> jconnor-scheduled-content
    def create_unit_update_schedule(self, consumer_id, units, update_options, schedule_data):
        """
        Create a schedule for updating content units on a consumer.
        @param consumer_id: unique id for the consumer
        @param units: list of unit type and unit key dicts
        @param update_options: options to pass to the update manager
        @param schedule_data: scheduling data
        @return: schedule id
        """
<<<<<<< HEAD
        self._validate_consumer(consumer_id)
        schedule_utils.validate_keys(update_options, _UNIT_OPTION_KEYS)
        if 'schedule' not in schedule_data:
            raise pulp_exceptions.MissingValue(['schedule'])

        manager = managers_factory.consumer_agent_manager()
        args = [consumer_id]
        kwargs = {'units': units,
                  'options': update_options.get('options', {})}
        weight = pulp_config.config.getint('tasks', 'consumer_content_weight')
        tags = [resource_tag(dispatch_constants.RESOURCE_CONSUMER_TYPE, consumer_id),
                action_tag('unit_update'), action_tag('scheduled_unit_update')]
        call_request = CallRequest(manager.update_content, args, kwargs, weight=weight, tags=tags, archive=True)
        call_request.reads_resource(dispatch_constants.RESOURCE_CONSUMER_TYPE, consumer_id)

        scheduler = dispatch_factory.scheduler()
        schedule_id = scheduler.add(call_request, **schedule_data)
        return schedule_id

    def update_unit_update_schedule(self, consumer_id, schedule_id, units=None, update_options=None, schedule_data=None):
        """
        Update an existing schedule for updating content units on a consumer.
        @param consumer_id: unique id for the consumer
        @param schedule_id: unique id for the schedule
        @param units: optional list of units to update
        @param update_options: optional options to pass to the update manager
        @param schedule_data: optional schedule updates
        """
        self._validate_consumer(consumer_id)
        schedule_updates = copy.copy(schedule_data) or {}

        scheduler = dispatch_factory.scheduler()
        report = scheduler.get(schedule_id)
        call_request = report['call_request']

        if units is not None:
            call_request.kwargs['units'] = units
            schedule_updates['call_request'] = call_request

        if update_options is not None and 'options' in update_options:
            call_request.kwargs['options'] = update_options['options']
            schedule_updates['call_request'] = call_request

        scheduler.update(schedule_id, **schedule_updates)

=======
        manager = managers_factory.consumer_agent_manager()
        return self._create_schedule(manager.update_content, UNIT_UPDATE_ACTION, consumer_id, units, update_options, schedule_data)

    def update_unit_update_schedule(self, consumer_id, schedule_id, units=None, update_options=None, schedule_data=None):
        """
        Update an existing schedule for updating content units on a consumer.
        @param consumer_id: unique id for the consumer
        @param schedule_id: unique id for the schedule
        @param units: optional list of units to update
        @param update_options: optional options to pass to the update manager
        @param schedule_data: optional schedule updates
        """
        return self._update_schedule(consumer_id, schedule_id, units, update_options, schedule_data)

>>>>>>> jconnor-scheduled-content
    def delete_unit_update_schedule(self, consumer_id, schedule_id):
        """
        Delete an existing schedule for updating content units on a consumer.
        @param consumer_id: unique id of the consumer
        @param schedule_id: unique id of the schedule
        """
<<<<<<< HEAD
        self._validate_consumer(consumer_id)

        scheduler = dispatch_factory.scheduler()
        scheduler.remove(schedule_id)
=======
        return self._delete_schedule(consumer_id, schedule_id)
>>>>>>> jconnor-scheduled-content

    def delete_all_unit_update_schedules(self, consumer_id):
        """
        Delete all unit update schedules for a consumer.
        Useful for unassociating consumers from the server.
        @param consumer_id: unique id of the consumer
        """
<<<<<<< HEAD
        self._validate_consumer(consumer_id)

        scheduler = dispatch_factory.scheduler()
        consumer_tag = resource_tag(dispatch_constants.RESOURCE_CONSUMER_TYPE, consumer_id)
        update_tag = action_tag('unit_update')
        reports = scheduler.find(consumer_tag, update_tag)

        for r in reports:
            scheduler.remove(r['call_report']['schedule_id'])
=======
        return self._delete_all_schedules(UNIT_UPDATE_ACTION, consumer_id)
>>>>>>> jconnor-scheduled-content

# consumer content uninstall schedule manager ----------------------------------

class ConsumerContentUninstallScheduleManager(ConsumerScheduleManager):

    def create_unit_uninstall_schedule(self, consumer_id, units, uninstall_options, schedule_data):
        """
        Create a schedule for uninstalling content units on a consumer.
        @param consumer_id: unique id for the consumer
        @param units: list of unit type and unit key dicts
        @param uninstall_options: options to pass to the uninstall manager
        @param schedule_data: scheduling data
        @return: schedule id
        """
<<<<<<< HEAD
        self._validate_consumer(consumer_id)
        schedule_utils.validate_keys(uninstall_options, _UNIT_OPTION_KEYS)
        if 'schedule' not in schedule_data:
            raise pulp_exceptions.MissingValue(['schedule'])

        manager = managers_factory.consumer_agent_manager()
        args = [consumer_id]
        kwargs = {'units': units,
                  'options': uninstall_options.get('options', {})}
        weight = pulp_config.config.getint('tasks', 'consumer_content_weight')
        tags = [resource_tag(dispatch_constants.RESOURCE_CONSUMER_TYPE, consumer_id),
                action_tag('unit_uninstall'), action_tag('scheduled_unit_uninstall')]
        call_request = CallRequest(manager.uninstall_content, args, kwargs, weight=weight, tags=tags, archive=True)
        call_request.reads_resource(dispatch_constants.RESOURCE_CONSUMER_TYPE, consumer_id)

        scheduler = dispatch_factory.scheduler()
        schedule_id = scheduler.add(call_request, **schedule_data)
        return schedule_id
=======
        manager = managers_factory.consumer_agent_manager()
        return self._create_schedule(manager.uninstall_content, UNIT_UNINSTALL_ACTION, consumer_id, units, uninstall_options, schedule_data)
>>>>>>> jconnor-scheduled-content

    def update_unit_uninstall_schedule(self, consumer_id, schedule_id, units=None, uninstall_options=None, schedule_data=None):
        """
        Update an existing schedule for uninstalling content units on a consumer.
        @param consumer_id: unique id for the consumer
        @param schedule_id: unique id for the schedule
        @param units: optional list of units to uninstall
        @param uninstall_options: optional options to pass to the uninstall manager
        @param schedule_data: optional schedule updates
        """
<<<<<<< HEAD
        self._validate_consumer(consumer_id)
        schedule_updates = copy.copy(schedule_data) or {}

        scheduler = dispatch_factory.scheduler()
        report = scheduler.get(schedule_id)
        call_request = report['call_request']

        if units is not None:
            call_request.kwargs['units'] = units
            schedule_updates['call_request'] = call_request

        if uninstall_options is not None and 'options' in uninstall_options:
            call_request.kwargs['options'] = uninstall_options['options']
            schedule_updates['call_request'] = call_request

        scheduler.update(schedule_id, **schedule_updates)
=======
        return self._update_schedule(consumer_id, schedule_id, units, uninstall_options, schedule_data)
>>>>>>> jconnor-scheduled-content

    def delete_unit_uninstall_schedule(self, consumer_id, schedule_id):
        """
        Delete an existing schedule for uninstalling content units on a consumer.
        @param consumer_id: unique id of the consumer
        @param schedule_id: unique id of the schedule
        """
<<<<<<< HEAD
        self._validate_consumer(consumer_id)

        scheduler = dispatch_factory.scheduler()
        scheduler.remove(schedule_id)
=======
        return self._delete_schedule(consumer_id, schedule_id)
>>>>>>> jconnor-scheduled-content

    def delete_all_unit_uninstall_schedules(self, consumer_id):
        """
        Delete all unit uninstall schedules for a consumer.
        Useful for unassociating consumers from the server.
        @param consumer_id: unique id of the consumer
        """
<<<<<<< HEAD
        self._validate_consumer(consumer_id)

        scheduler = dispatch_factory.scheduler()
        consumer_tag = resource_tag(dispatch_constants.RESOURCE_CONSUMER_TYPE, consumer_id)
        uninstall_tag = action_tag('unit_uninstall')
        reports = scheduler.find(consumer_tag, uninstall_tag)

        for r in reports:
            scheduler.remove(r['call_report']['schedule_id'])
=======
        return self._delete_all_schedules(UNIT_UNINSTALL_ACTION, consumer_id)
>>>>>>> jconnor-scheduled-content

