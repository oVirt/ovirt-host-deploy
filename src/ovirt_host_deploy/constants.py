#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2012-2015 Red Hat, Inc.
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


import os


from otopi import util


@util.export
class FileLocations(object):
    OVIRT_HOST_DEPLOY_CONFIG_FILE = '/etc/ovirt-host-deploy.conf'

    OVIRT_HOST_DEPLOY_LOG_PREFIX = 'ovirt-host-deploy'
    VDSM_CONFIG_FILE = '/etc/vdsm/vdsm.conf'
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

    OPENSTACK_NEUTRON_CONFIG = '/etc/neutron/neutron.conf'
    OPENSTACK_NEUTRON_PLUGIN_CONFIG = '/etc/neutron/plugin.ini'
    OPENSTACK_NEUTRON_LINUXBRIDGE_CONFIG = \
        '/etc/neutron/plugins/linuxbridge/linuxbridge_conf.ini'
    if os.path.exists('/etc/neutron/plugins/ml2/openvswitch_agent.ini'):
        # OpenStack Liberty or newer
        OPENSTACK_NEUTRON_OPENVSWITCH_CONFIG = \
            '/etc/neutron/plugins/ml2/openvswitch_agent.ini'
    else:
        # OpenStack Kilo or older
        OPENSTACK_NEUTRON_OPENVSWITCH_CONFIG = \
            '/etc/neutron/plugins/openvswitch/ovs_neutron_plugin.ini'
    NRPE_CONFIG_FILE = '/etc/nagios/nrpe.cfg'

    KDUMP_CONFIG_FILE = '/etc/kdump.conf'

    VMCONSOLE_STORE = '/etc/pki/ovirt-vmconsole'
    VMCONSOLE_CA_FILE = os.path.join(VMCONSOLE_STORE, 'ca.pub')
    VMCONSOLE_CERT_FILE = os.path.join(
        VMCONSOLE_STORE,
        'host-ssh_host_rsa-cert.pub',
    )
    VMCONSOLE_KEY_FILE = os.path.join(VMCONSOLE_STORE, 'host-ssh_host_rsa')
    VMCONSOLE_KEY_PENDING_FILE = os.path.join(
        VMCONSOLE_STORE,
        'host-ssh_host_rsa.pending',
    )
    HOSTED_ENGINE_CONF = '/etc/ovirt-hosted-engine/hosted-engine.conf'
    OVIRT_NODE_OS_FILE = '/etc/os-release'
    OVIRT_NODE_VARIANT_KEY = 'VARIANT_ID'
    OVIRT_NODE_VARIANT_VAL = 'ovirt-node'


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

    VMCONSOLE_SUPPORT_NONE = 0
    VMCONSOLE_SUPPORT_V1 = 1

    HOSTED_ENGINE_ACTION_DEPLOY = 'deploy'
    HOSTED_ENGINE_ACTION_REMOVE = 'remove'
    HOSTED_ENGINE_ACTION_NONE = 'none'


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
class KernelEnv(object):
    CMDLINE_NEW = 'KERNEL/cmdlineNew'
    CMDLINE_OLD = 'KERNEL/cmdlineOld'


@util.export
@util.codegen
class KdumpEnv(object):
    ENABLE = 'KDUMP/enable'
    SUPPORTED = 'KDUMP/supported'
    DESTINATION_ADDRESS = 'KDUMP/destinationAddress'
    DESTINATION_PORT = 'KDUMP/destinationPort'
    MESSAGE_INTERVAL = 'KDUMP/messageInterval'


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
    CHECK_VIRT_HARDWARE = 'VDSM/checkVirtHardware'
    OVIRT_NODE = 'VDSM/ovirt-node'
    OVIRT_VINTAGE_NODE = 'VDSM/ovirt-legacy-node'
    OVIRT_NODE_HAS_OWN_BRIDGES = 'VDSM/nodeHasOwnBridges'
    NODE_PLUGIN_VDSM_FEATURES = 'VDSM/nodePluginVdsmFeatures'
    CONFIG_OVERRIDE = 'VDSM/configOverride'
    DISABLE_NETWORKMANAGER = 'VDSM/disableNetworkManager'
    CONFIG_PREFIX = 'VDSM_CONFIG/'


@util.export
@util.codegen
class VMConsoleEnv(object):
    SUPPORT = 'VMCONSOLE/support'
    ENABLE = 'VMCONSOLE/enable'
    CAKEY = 'VMCONSOLE/caKey'
    KEY_SIZE = 'VMCONSOLE/keySize'
    CERTIFICATE = 'VMCONSOLE/certificate'
    CERTIFICATE_ENROLLMENT = 'VMCONSOLE/certificateEnrollment'


@util.export
@util.codegen
class VirtEnv(object):
    ENABLE = 'VIRT/enable'


@util.export
@util.codegen
class GlusterEnv(object):
    ENABLE = 'GLUSTER/enable'
    MONITORING_ENABLE = 'GLUSTER/monitoringEnable'
    MONITORING_SERVER = 'GLUSTER/monitoringServer'


@util.export
@util.codegen
class TuneEnv(object):
    TUNED_PROFILE = 'TUNE/tunedProfile'


@util.export
@util.codegen
class HostedEngineEnv(object):
    ACTION = 'HOSTED_ENGINE/action'
    HOSTED_ENGINE_CONFIG_PREFIX = 'HOSTED_ENGINE_CONFIG/'


@util.export
@util.codegen
class OpenStackEnv(object):
    NEUTRON_ENABLE = 'OPENSTACK/neutronEnable'
    NEUTRON_CONFIG_PREFIX = 'OPENSTACK_NEUTRON_CONFIG/'
    NEUTRON_LINUXBRIDGE_ENABLE = 'OPENSTACK/neutronLinuxBridgeEnable'
    NEUTRON_LINUXBRIDGE_CONFIG_PREFIX = 'OPENSTACK_NEUTRON_LINUXBRIDGE_CONFIG/'
    NEUTRON_OPENVSWITCH_ENABLE = 'OPENSTACK/neutronOpenvswitchEnable'
    NEUTRON_OPENVSWITCH_INTERNAL_BRIDGE = \
        'OPENSTACK/neutronOpenvswitchIntegrationBridge'
    NEUTRON_OPENVSWITCH_CONFIG_PREFIX = 'OPENSTACK_NEUTRON_OPENVSWITCH_CONFIG/'


@util.export
@util.codegen
class Queries(object):
    CERTIFICATE_CHAIN = 'VDSM_CERTIFICATE_CHAIN'
    VMCONSOLE_CERTIFICATE = 'VMCONSOLE_CERTIFICATE'


@util.export
@util.codegen
class Displays(object):
    CERTIFICATE_REQUEST = 'VDSM_CERTIFICATE_REQUEST'
    VMCONSOLE_CERTIFICATE_REQUEST = 'VMCONSOLE_CERTIFICATE_REQUEST'


@util.export
@util.codegen
class Confirms(object):
    DEPLOY_PROCEED = 'DEPLOY_PROCEED'


@util.export
class Stages(object):
    VDSM_STARTED = 'odeploycons.packages.vdsm.started'


# vim: expandtab tabstop=4 shiftwidth=4
