# Copyright (c) 2010 OpenStack Foundation
# Copyright 2010 United States Government as represented by the
# Administrator of the National Aeronautics and Space Administration.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.

"""
Chance (Random) Scheduler implementation
"""

import random

from oslo_config import cfg

from nova import exception
from nova.i18n import _
from nova.scheduler import driver

CONF = cfg.CONF
CONF.import_opt('compute_topic', 'nova.compute.rpcapi')


class ChanceScheduler(driver.Scheduler):
    """Implements Scheduler as a random node selector."""

    def _filter_hosts(self, request_spec, hosts, filter_properties):
        """Filter a list of hosts based on request_spec."""

        ignore_hosts = filter_properties.get('ignore_hosts', [])
        hosts = [host for host in hosts if host not in ignore_hosts]
        return hosts

    def _schedule(self, context, topic, request_spec, filter_properties):
        """Picks a host that is up at random."""

        elevated = context.elevated()
        hosts = self.hosts_up(elevated, topic)
        if not hosts:
            msg = _("Is the appropriate service running?")
            raise exception.NoValidHost(reason=msg)

        hosts = self._filter_hosts(request_spec, hosts, filter_properties)
        if not hosts:
            msg = _("Could not find another compute")
            raise exception.NoValidHost(reason=msg)

        return random.choice(hosts)

    def select_destinations(self, context, request_spec, filter_properties):
        """Selects random destinations."""
        num_instances = request_spec['num_instances']
        # NOTE(timello): Returns a list of dicts with 'host', 'nodename' and
        # 'limits' as keys for compatibility with filter_scheduler.
        dests = []
        for i in range(num_instances):
            host = self._schedule(context, CONF.compute_topic,
                    request_spec, filter_properties)
            host_state = dict(host=host, nodename=None, limits=None)
            dests.append(host_state)

        if len(dests) < num_instances:
            reason = _('There are not enough hosts available.')
            raise exception.NoValidHost(reason=reason)
        return dests
