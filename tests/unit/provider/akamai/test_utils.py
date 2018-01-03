# Copyright (c) 2016 Rackspace, Inc.
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

import mock

from poppy.provider.akamai import utils
from tests.unit import base


class TestAkamaiUtils(base.TestCase):

    def setUp(self):
        super(TestAkamaiUtils, self).setUp()

        conn_patch = mock.patch("OpenSSL.SSL.Connection")
        self.mock_ssl_conn = conn_patch.start()
        self.addCleanup(conn_patch.stop)

        sub_alt = mock.patch(
            "poppy.provider.akamai.utils.get_subject_alternates"
        )
        self.mock_sub_alt = sub_alt.start()
        self.addCleanup(sub_alt.stop)

        self.mock_sub_alt.return_value = ['secured1.sni1.altcdn.com']

    def test_get_ssl_positive(self):
        self.assertEqual(
            1, utils.get_ssl_number_of_hosts_alternate('remote_host')
        )
        self.assertEqual(
            ['secured1.sni1.altcdn.com'],
            utils.get_sans_by_host_alternate('remote_host')
        )

    def test_get_ssl_number_of_hosts_alternate(self):
        self.assertEqual(
            1, utils.get_ssl_number_of_hosts_alternate('remote_host')
        )

    def test_get_sans_by_host_alternate(self):
        self.assertEqual(
            ['secured1.sni1.altcdn.com'],
            utils.get_sans_by_host_alternate('remote_host')
        )
