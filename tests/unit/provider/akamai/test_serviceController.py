from unittest import TestCase
import ddt
import mock
import uuid

from nose.tools import assert_true

from poppy.provider.akamai import services
from tests.unit import base
from poppy.model.helpers import domain
from poppy.model.helpers import origin
from poppy.model.service import Service
from poppy.model import service


# from poppy.provider.akamai import driver

@ddt.ddt
class TestServiceController(base.TestCase):
    def setUp(self):

        super(TestServiceController, self).setUp()
        driver_patcher = mock.patch('poppy.provider.akamai.driver')
        mock_driver = driver_patcher.start()
        self.addCleanup(driver_patcher.stop)
        self.driver = mock_driver()
        self.policy_client = self.driver.policy_api_client
        self.ccu_client = self.driver.ccu_api_client
        self.driver.provider_name = 'Akamai'
        self.driver.http_conf_number = 1
        self.driver.akamai_https_access_url_suffix = str(uuid.uuid1())
        self.driver.akamai_http_access_url_suffix = str(uuid.uuid1())
        self.driver.akamai_access_url_link = "abc.com.test.edgesuite.net"
        self.san_cert_cnames = [str(x) for x in range(7)]
        self.driver.san_cert_cnames = self.san_cert_cnames
        self.driver.metrics_resolution = 86400
        self.controller = services.ServiceController(self.driver)
        service_id = str(uuid.uuid4())
        domains_old = domain.Domain(domain='cdn.poppy.org')
        current_origin = origin.Origin(origin='poppy.org')
        self.service_obj = Service(service_id=service_id,
                                   name='poppy cdn service',
                                   domains=[domains_old],
                                   origins=[current_origin],
                                   flavor_id='cdn')

    def test_get_provider_access_url_shared_custom(self):

        certificates = ["shared", "custom"]
        for certificate in certificates:
            _domain = domain.Domain('densely.sage.com', 'https', certificate=certificate)
            dp = 'test.xxxx.secure.raxcdn.com'
            edge_host_name = None
            https_url = self.controller._get_provider_access_url(_domain, dp, edge_host_name)
            if certificate == 'shared':
                expected_out = 'xxxx.secure.raxcdn.com.' + self.driver.akamai_https_access_url_suffix
            else:
                expected_out = 'test.xxxx.secure.raxcdn.com.' + self.driver.akamai_https_access_url_suffix
            self.assertEqual(https_url, expected_out)

    def test_get_provider_access_url_san_sni(self):
        certificates = ["san", "sni"]
        for certificate in certificates:
            _domain = domain.Domain('densely.sage.com', 'https', certificate=certificate)
            dp = 'test.abc.com'
            edge_host_name = "test.com"
            https_url = self.controller._get_provider_access_url(_domain, dp, edge_host_name)
            expected_out = 'test.com.' + self.driver.akamai_https_access_url_suffix
            self.assertEqual(https_url, expected_out)

    def test_get_provider_access_url_http(self):

        _domain = domain.Domain('densely.sage.com', 'http', certificate=None)
        dp = 'test.abc.com'
        edge_host_name = None
        http_url = self.controller._get_provider_access_url(_domain, dp, edge_host_name)
        expected_out = 'abc.com.test.edgesuite.net'
        self.assertEqual(http_url, expected_out)



