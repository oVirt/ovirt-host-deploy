#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2012-2013 Red Hat, Inc.
#
# This library is free software; you can redistribute it and/or
# modify it under the terms of the GNU Lesser General Public
# License as published by the Free Software Foundation; either
# version 2.1 of the License, or (at your option) any later version.
#
# This library is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
# Lesser General Public License for more details.
#
# You should have received a copy of the GNU Lesser General Public
# License along with this library; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
#


"""Constants."""


from otopi import util


@util.export
class FileLocations(object):
    OVIRT_HOST_DEPLOY_CONFIG_FILE = '/etc/ovirt-host-deploy.conf'

    OVIRT_HOST_DEPLOY_LOG_PREFIX = 'ovirt-host-deploy'
    VDSM_CONFIG_FILE = '/etc/vdsm/vdsm.conf'
    VDSM_FORCE_RECONFIGURE = '/var/lib/vdsm/reconfigure'
    VDSM_TRUST_STORE = '/etc/pki/vdsm'
    VDSM_CA_FILE = 'certs/cacert.pem'
    VDSM_CERT_FILE = 'certs/vdsmcert.pem'
    VDSM_KEY_FILE = 'keys/vdsmkey.pem'
    VDSM_KEY_PENDING_FILE = 'keys/vdsmkey.pending.pem'
    VDSM_SPICE_CA_FILE = 'libvirt-spice/ca-cert.pem'
    VDSM_SPICE_CERT_FILE = 'libvirt-spice/server-cert.pem'
    VDSM_SPICE_KEY_FILE = 'libvirt-spice/server-key.pem'
    VDSM_ID_FILE = '/etc/vdsm/vdsm.id'

    # vdsm does not configure libvirt client
    # so libvirt client accesses the default locations.
    LIBVIRT_DEFAULT_TRUST_STORE = '/etc/pki/libvirt'
    LIBVIRT_DEFAULT_CLIENT_CA_FILE = '../CA/cacert.pem'
    LIBVIRT_DEFAULT_CLIENT_CERT_FILE = 'clientcert.pem'
    LIBVIRT_DEFAULT_CLIENT_KEY_FILE = 'private/clientkey.pem'

    VDSM_DATA_DIR = '/usr/share/vdsm'

    HOOKS_DIR = '/usr/libexec/vdsm/hooks'
    HOOKS_PLUGIN_HOOKS_DIR = 'hooks.d'
    HOOKS_PLUGIN_PACKAGES_DIR = 'packages.d'


@util.export
class Defaults(object):
    DEFAULT_KEY_SIZE = 2048


@util.export
@util.codegen
class Const(object):
    CERTIFICATE_ENROLLMENT_NONE = 'none'
    CERTIFICATE_ENROLLMENT_INLINE = 'inline'
    CERTIFICATE_ENROLLMENT_REQUEST = 'request'
    CERTIFICATE_ENROLLMENT_ACCEPT = 'accept'


@util.export
@util.codegen
class CoreEnv(object):
    INTERFACE_VERSION = 'ODEPLOY/INTERFACE_VERSION'
    FORCE_REBOOT = 'ODEPLOY/forceReboot'
    INSTALL_INCOMPLETE = 'ODEPLOY/installIncomplete'
    INSTALL_INCOMPLETE_REASONS = 'ODEPLOY/installIncompleteReasons'
    OFFLINE_PACKAGER = 'ODEPLOY/offlinePackager'


@util.export
@util.codegen
class VdsmEnv(object):
    VDSM_MINIMUM_VERSION = 'VDSM/vdsmMinimumVersion'
    CERTIFICATE_ENROLLMENT = 'VDSM/certificateEnrollment'
    CERTIFICATE_CHAIN = 'VDSM/certificateChain'
    KEY_SIZE = 'VDSM/keySize'
    VDSM_ID = 'VDSM/vdsmId'
    ENGINE_HOST = 'VDSM/engineHost'
    ENGINE_ADDRESS = 'VDSM/engineAddress'
    ENGINE_PORT = 'VDSM/enginePort'
    CONNECTION_TIMEOUT = 'VDSM/connectionTimeout'
    CONNECTION_RETRIES = 'VDSM/connectionRetries'
    MANAGEMENT_BRIDGE_NAME = 'VDSM/managementBridgeName'
    CHECK_VIRT_HARDWARE = 'VDSM/checkVirtHardware'
    OVIRT_NODE = 'VDSM/node'
    CONFIG_OVERRIDE = 'VDSM/configOverride'
    CONFIG_PREFIX = 'VDSM_CONFIG/'


@util.export
@util.codegen
class GlusterEnv(object):
    ENABLE = 'GLUSTER/enable'


@util.export
@util.codegen
class Queries(object):
    CERTIFICATE_CHAIN = 'VDSM_CERTIFICATE_CHAIN'


@util.export
@util.codegen
class Displays(object):
    CERTIFICATE_REQUEST = 'VDSM_CERTIFICATE_REQUEST'


@util.export
@util.codegen
class Confirms(object):
    DEPLOY_PROCEED = 'DEPLOY_PROCEED'


# vim: expandtab tabstop=4 shiftwidth=4
