# Copyright (c) 2014 Rackspace, Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#    http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or
# implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import time

from oslo.config import cfg
from taskflow import task

from poppy import bootstrap
from poppy.openstack.common import log
from poppy.transport.pecan.models.request import (
    provider_details as req_provider_details
)

LOG = log.getLogger(__name__)

conf = cfg.CONF
conf(project='poppy', prog='poppy', args=[])


class DeleteProviderServicesTask(task.Task):
    default_provides = "responders"

    def execute(self, provider_details):
        bootstrap_obj = bootstrap.Bootstrap(conf)
        service_controller = bootstrap_obj.manager.services_controller
        provider_details = json.loads(provider_details)

        responders = []
        # try to delete all service from each provider presented
        # in provider_details
        for provider in provider_details:
            provider_details[provider] = (
                req_provider_details.load_from_json(provider_details[provider])
            )
            LOG.info('Starting to delete service from {0}'.format(provider))
            responder = service_controller.provider_wrapper.delete(
                service_controller._driver.providers[provider.lower()],
                provider_details)
            responders.append(responder)
            LOG.info('Deleting service from {0} complete...'.format(provider))
        return responders


class DeleteServiceDNSMappingTask(task.Task):
    default_provides = "dns_responder"

    def execute(self, provider_details, retry_sleep_time):
        time.sleep(retry_sleep_time)
        bootstrap_obj = bootstrap.Bootstrap(conf)
        service_controller = bootstrap_obj.manager.services_controller

        provider_details = json.loads(provider_details)
        for provider in provider_details:
            provider_details[provider] = (
                req_provider_details.load_from_json(provider_details[provider])
                )

        # delete associated cname records from DNS
        dns_responder = service_controller.dns_controller.delete(
            provider_details)
        for provider_name in dns_responder:
            if 'error' in dns_responder[provider_name].keys():
                LOG.info('Deleting DNS for {0} failed!'.format(provider_name))
                raise Exception('DNS Deletion Failed')

        return dns_responder

    def revert(self, provider_details, retry_sleep_time, **kwargs):
        LOG.info('Sleeping for {0} minutes and '
                 'retrying'.format(retry_sleep_time))


class GatherProviderDetailsTask(task.Task):
    default_provides = "provider_details_dict"

    def execute(self, responders, dns_responder, provider_details):
        provider_details = json.loads(provider_details)
        for provider in provider_details:
            provider_details[provider] = (
                req_provider_details.load_from_json(provider_details[provider])
                )

        for responder in responders:
            provider_name = list(responder.items())[0][0]

            if 'error' in responder[provider_name]:
                LOG.info('Delete service from {0}'
                         'failed'.format(provider_name))
                # stores the error info for debugging purposes.
                provider_details[provider_name].error_info = (
                    responder[provider_name].get('error_info'))
            elif 'error' in dns_responder[provider_name]:
                LOG.info('Delete service from DNS failed')
                # stores the error info for debugging purposes.
                provider_details[provider_name].error_info = (
                    dns_responder[provider_name].get('error_info'))
            else:
                # delete service successful, remove this provider detail record
                del provider_details[provider_name]

        for provider in provider_details:
            provider_details[provider] = provider_details[provider].to_dict()

        return provider_details


class DeleteStorageServiceTask(task.Task):

    def execute(self, project_id, service_id):
        bootstrap_obj = bootstrap.Bootstrap(conf)
        service_controller = bootstrap_obj.manager.services_controller
        service_controller.storage_controller.delete(project_id, service_id)