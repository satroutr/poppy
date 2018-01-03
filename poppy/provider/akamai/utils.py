# Copyright (c) 2013 Rackspace, Inc.
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

import socket
import sys

from kazoo import client
from ndg.httpsclient.subj_alt_name import SubjectAltName
from OpenSSL import SSL
from oslo_log import log
from pyasn1.codec.der import decoder as der_decoder

LOG = log.getLogger(__name__)


def pyopenssl_callback(conn, cert, errno, depth, ok):
    """Callback method for _get_cert_alternate"""

    if depth == 0 and (errno == 9 or errno == 10):
        return False
    return True


def _get_cert_alternate(remote_host):
    """Create SSL context and get x509 certificate object

    :param remote_host: remote host name that contains the certificate
    :returns :x509 certificate object
    """

    try:
        context = SSL.Context(SSL.TLSv1_METHOD)
        context.set_options(SSL.OP_NO_SSLv2)
        context.set_options(SSL.OP_NO_SSLv3)
        context.set_verify(
            SSL.VERIFY_PEER | SSL.VERIFY_FAIL_IF_NO_PEER_CERT,
            pyopenssl_callback
        )
        conn = SSL.Connection(context, socket.socket(socket.AF_INET))
        conn.connect((remote_host, 443))
        conn.set_connect_state()
        conn.set_tlsext_host_name(remote_host)
        conn.do_handshake()
        cert = conn.get_peer_certificate()
        conn.close()

        return cert
    except Exception as exc:
        LOG.info(
            "Error retrieving sans for {0}, with exception {1}"
            .format(remote_host, exc)
        )
        raise ValueError(
            'Get remote host certificate {0} info failed.'.format(remote_host))


def get_subject_alternates(cert):
    """Get the subject alternates from a x509 object

    :param cert: x509 certificate object
    :returns: list of subject alternates residing on x509 object
    """

    general_names = SubjectAltName()
    subject_alternates = []

    for items in range(cert.get_extension_count()):
        ext = cert.get_extension(items)
        if ext.get_short_name() == 'subjectAltName':
            ext_dat = ext.get_data()
            decoded_dat = der_decoder.decode(ext_dat, asn1Spec=general_names)

            for name in decoded_dat:
                if isinstance(name, SubjectAltName):
                    for entry in range(len(name)):
                        component = name.getComponentByPosition(entry)
                        subject_alternates.append(
                            str(component.getComponent())
                        )
    return subject_alternates


def get_ssl_number_of_hosts_alternate(remote_host):
    """Get number of Alternative names for a (SNI) Cert."""

    LOG.info("Checking number of hosts for {0}".format(remote_host))

    cert = _get_cert_alternate(remote_host)

    return len(get_subject_alternates(cert))


def get_sans_by_host_alternate(remote_host):
    """Get Subject Alternative Names for a (SNI) Cert."""

    LOG.info("Retrieving sans for {0}".format(remote_host))

    cert = _get_cert_alternate(remote_host)

    return get_subject_alternates(cert)


def connect_to_zookeeper_storage_backend(conf):
    """Connect to a zookeeper cluster"""
    storage_backend_hosts = ','.join(['%s:%s' % (
        host, conf.storage_backend_port)
        for host in
        conf.storage_backend_host])
    zk_client = client.KazooClient(storage_backend_hosts)
    zk_client.start()
    return zk_client


def connect_to_zookeeper_queue_backend(conf):
    """Connect to a zookeeper cluster"""
    storage_backend_hosts = ','.join(['%s:%s' % (
        host, conf.queue_backend_port)
        for host in
        conf.queue_backend_host])
    zk_client = client.KazooClient(storage_backend_hosts)
    zk_client.start()
    return zk_client


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print('Usage: %s <remote_host_you_want_get_cert_on>' % sys.argv[0])
        sys.exit(0)
    print("There are %s DNS names for SAN Cert on %s" % (
        get_ssl_number_of_hosts_alternate(sys.argv[1]), sys.argv[1]))
