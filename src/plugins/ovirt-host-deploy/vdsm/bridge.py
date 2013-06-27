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


"""vdsm management bridge plugin."""


import os
import time
import re
import shlex
import socket
import struct
import select
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import util
from otopi import plugin


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """Setup bridge networking.

    NOTE: no rollback in case of failure.

    This module should be retired in favour of engine create all bridges.

    Environment:
        VdsmEnv.ENGINE_HOST -- host name.
        VdsmEnv.ENGINE_ADDRESS -- address (resolved) optional.
        VdsmEnv.ENGINE_PORT -- port to connect.
        VdsmEnv.CONNECTION_TIMEOUT -- timeout for tcp connect.
        VdsmEnv.CONNECTION_RETRIES -- connect retries to establish route.
        VdsmEnv.MANAGEMENT_BRIDGE_NAME -- management bridge name.

    """

    """
    3: wlan0: <BROADCAST,MULTICAST,UP,LOWER_UP> mtu 1500 qdisc mq state UP...
        link/ether 00:0e:bf:44:0d:1f brd ff:ff:ff:ff:ff:ff
            inet 192.168.0.104/24 brd 192.168.0.255 scope global wlan0
    """
    _RE_IPROUTE_ADDR_SHOW = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            \s+
            (inet|inet6)
            \s+
            (?P<address>[\da-f.:]+)/\d+
            .*
            scope
            \s+
            global
            \s+
            (?P<interface>\S+)
        """
    )

    """
    Remote:
        192.168.1.1 via 192.168.0.1 dev wlan0  src 192.168.0.104
            cache
    Local:
        local 192.168.0.104 dev lo  src 192.168.0.104
            cache <local>
    """
    _RE_IPROUTE_ROUTE_GET = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            ((?P<local>local)\s+|)
            (?P<address>[\da-f.:]+)
            \s+
            (
                via
                \s+
                ([\da-f.:]+)
                \s+
                |
            )
            dev
            \s+
            (?P<device>\S+)
            \s+
            src
            \s+
            ([\da-f.:]+)
        """
    )

    _RE_VLAN_ID = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            .*
            \sVID:\s(?P<vlan>\d+)\s
            .*
            """
    )

    _RE_VLAN_DEVICE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            Device:
            \s+
            (?P<device>\S+)
            \s*
            $
            """
    )

    """
    IP4.ADDRESS[1]:       ip = 10.35.1.115/23, gw = 10.35.1.254
    """
    _RE_NM_LIST_IF_IP = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            IP4\.ADDRESS\[1\]:
            \s+
            ip\s*=\s*(?P<address>[\d.]+)/(?P<prefix>\d+),
            \s*
            gw\s*=\s*(?P<gateway>[\d.]+)
        """
    )

    _INTERFACE_LOOPBACK = 'lo'

    def _waitForRoute(self, host, timeout, retries):
        """Wait for route to be available.

        Keywords arguments:
        host -- (host, port).
        timeout -- connect timeout.
        retries -- number of retries.

        NOTE: This function throws an exception also if connection fails.

        """
        EHOSTUNREACH = 113
        ENETUNREACH = 101
        EINPROGRESS = 115

        self.logger.debug(
            'host=%s, timeout=%s, retries=%s',
            host,
            timeout,
            retries
        )

        success = False
        fail = False
        count = 0
        while not success and not fail and count < retries:
            count += 1
            s = -1
            try:
                s = socket.socket()
                s.setblocking(0)
                errno = s.connect_ex(host)
                self.logger.debug('connect errno %s' % errno)
                if errno == 0:
                    success = True
                elif errno == EINPROGRESS:
                    # select does not return e properly.
                    (r, w, e) = select.select([s], [s], [s], timeout)
                    self.logger.debug('select result %s %s %s' % (r, w, e))
                    if r or w or e:
                        errno = s.getsockopt(
                            socket.SOL_SOCKET,
                            socket.SO_ERROR
                        )
                        self.logger.debug('socket errno %s' % errno)
                        if errno == 0:
                            success = True
                        elif errno in (EHOSTUNREACH, ENETUNREACH):
                            self.logger.debug('EHOSTUNREACH, ENETUNREACH')
                        else:
                            self.logger.debug('fail')
                            fail = True
                    else:
                        # timeout
                        pass
                elif errno in (EHOSTUNREACH, ENETUNREACH):
                    self.logger.debug('EHOSTUNREACH, ENETUNREACH')
                else:
                    self.logger.debug('fail')
                    fail = True
            finally:
                if s != -1:
                    s.close()

            if not success and not fail:
                time.sleep(1)

        if not success:
            self.logger.debug('connect failed %s (failed=%s)', host, fail)
            raise RuntimeError(
                _('Cannot establish connection to {host}:{port}').format(
                    host=host[0],
                    port=host[1],
                )
            )

        self.logger.debug('connect established %s', host)

    def _interfaceExists(self, name):
        return os.path.exists(
            os.path.join(
                '/sys/class/net',
                name,
            )
        )

    def _interfaceIsBridge(self, name):
        return os.path.exists(
            os.path.join(
                '/sys/class/net',
                name,
                'bridge/bridge_id',
            )
        )

    def _interfaceIsBonding(self, name):
        return os.path.exists(
            os.path.join(
                '/sys/class/net',
                name,
                'bonding/mode',
            )
        )

    def _interfacesOfBridge(self, name):
        return os.listdir(
            os.path.join(
                '/sys/class/net',
                name,
                'brif',
            )
        )

    def _interfacesOfBonding(self, name):
        interfaces = []
        with open(
            os.path.join(
                '/sys/class/net',
                name,
                'bonding/slaves',
            ),
            'r'
        ) as f:
            s = f.read().strip()
            if s:
                interfaces = s.split(' ')
        return interfaces

    def _getInterfaceForDestination(self, address):

        self.logger.debug('determine interface for %s', address)

        rc, stdout, stderr = self.execute(
            (
                self.command.get('ip'),
                'route', 'get', 'to', address
            ),
        )
        if len(stdout) == 0:
            raise RuntimeError(
                _('Unable to determine route interface for {address}').format(
                    address=address
                )
            )

        m = self._RE_IPROUTE_ROUTE_GET.match(stdout[0])
        if m is None:
            raise RuntimeError(
                _('Unable to determine route interface for {address}').format(
                    address=address
                )
            )

        if m.group('address') != address:
            raise RuntimeError(
                _('Invalid route information for {address}').format(
                    address=address
                )
            )

        if m.group('local'):
            interface = self._INTERFACE_LOOPBACK
        else:
            interface = m.group('device')

        self.logger.debug('interface for %s is %s', address, interface)
        return interface

    def _getInterfaceToInstallBasedOnDestination(self, address):
        interface = self._getInterfaceForDestination(
            address=address
        )

        # this is required for all-in-one
        # we need to guess which interface to
        # bridge
        if interface == self._INTERFACE_LOOPBACK:
            rc, stdout, stderr = self.execute(
                (
                    self.command.get('ip'),
                    'addr', 'show',
                ),
            )
            for line in stdout:
                m = self._RE_IPROUTE_ADDR_SHOW.match(line)
                if (
                    m is not None and
                    m.group('address') == address
                ):
                    interface = m.group('interface')

        return interface

    def _getVlanMasterDevice(self, name):
        interface = None
        vlanid = None
        try:
            with open(
                os.path.join(
                    '/proc/net/vlan',
                    name
                ),
                'r'
            ) as f:
                for line in f:
                    m = self._RE_VLAN_ID.match(line)
                    if m is not None:
                        vlanid = m.group('vlan')
                    else:
                        m = self._RE_VLAN_DEVICE.match(line)
                        if m is not None:
                            interface = m.group('device')

            if interface is None or vlanid is None:
                raise RuntimeError(
                    _(
                        'Interface {interface} is VLAN interface, '
                        'however its configuration is unexpected'
                    ).format(
                        interface=name,
                    )
                )

        except IOError:
            # not vlan slave
            interface = name

        return (interface, vlanid)

    def _rhel_getInterfaceConfigParameters(self, name):

        self.logger.debug('Readig interface parameters of %s', name)

        ifcfg = '/etc/sysconfig/network-scripts/ifcfg-%s' % name
        parameters = []

        if os.path.exists(ifcfg):
            with open(ifcfg, 'r') as f:
                for line in f:
                    self.logger.debug('parameter %s', line)
                    line = line.strip()
                    if not line or line.startswith('#'):
                        pass
                    elif line.split('=', 1)[0].strip() in (
                        'DEVICE',
                        'HWADDR',
                        'NM_CONTROLLED',
                        'TYPE',
                    ):
                        pass
                    else:
                        try:
                            line = ''.join(shlex.split(line))
                        except:
                            self.logger.debug("Cannot parse line '%s'", line)
                        parameters.append(line)
        else:
            #
            # *EXPERIMENTAL*
            #
            # Try to handle network manager controlled
            # interface.
            #
            address = None
            gateway = None
            dhcp = False

            rc, stdout, stderr = self.execute(
                (self.command.get('nmcli'), 'dev', 'list', 'iface', name),
            )
            for l in stdout:
                if l.startswith('IP4.ADDRESS[1]:'):
                    r = self._RE_NM_LIST_IF_IP.match(l)
                    if r is not None:
                        address = r.group('address')
                        prefix = int(r.group('prefix'))
                        gateway = r.group('gateway')
                if l.startswith('DHCP4.OPTION[1]:'):
                    dhcp = True

            parameters.append('onboot=yes')
            if dhcp:
                parameters.append('bootproto=dhcp')
            elif address is not None:
                parameters.append('ipaddr=%s' % address)
                netmask = socket.inet_ntoa(
                    struct.pack(
                        "!I",
                        int(
                            (
                                ''.ljust(prefix, '1') +
                                ''.ljust(32 - prefix, '0')
                            ),
                            2
                        )
                    )
                )
                parameters.append('netmask=%s' % netmask)
                parameters.append('gateway=%s' % gateway)
            else:
                raise RuntimeError(
                    _('Unsupported network manager configuration')
                )

        self.logger.debug('parameters of %s: %s', name, parameters)
        return parameters

    def _removeBridge(self, name, interface):
        interface, vlanid = self._getVlanMasterDevice(name=interface)
        self.execute(
            (
                os.path.join(
                    odeploycons.FileLocations.VDSM_DATA_DIR,
                    'delNetwork',
                ),
                name,
                vlanid if vlanid is not None else '',
                '',     # bonding is not supported
                interface if interface is not None else '',
            ),
        )

        #
        # vdsm interface does not handle
        # ovirt node properly.
        # we should manually delete the
        # ifcfg file to avoid having duplicate
        # bridge.
        #
        if self.environment[odeploycons.VdsmEnv.OVIRT_NODE]:
            ifcfg = '/etc/sysconfig/network-scripts/ifcfg-%s' % (
                name
            )
            if os.path.exists(ifcfg):
                from ovirtnode import ovirtfunctions
                ovirtfunctions.ovirt_safe_delete_config(ifcfg)

    def _createBridge(self, name, interface, parameters):
        # WORKAROUND-BEGIN
        # firewalld conflicts with addNetwork causes to hang
        if self.services.exists('firewalld'):
            self.services.state('firewalld', False)
        # WORKAROUND-END

        bond = None

        # resolve master vlan interface
        interface, vlanid = self._getVlanMasterDevice(name=interface)

        # resolve bond interface
        if self._interfaceIsBonding(name=interface):
            bond = interface
            interface = ','.join(
                self._interfacesOfBonding(name=interface)
            )

        parameters = parameters[:] + ['blockingdhcp=true']
        self.execute(
            (
                [
                    os.path.join(
                        odeploycons.FileLocations.VDSM_DATA_DIR,
                        'addNetwork',
                    ),
                    name,
                    vlanid if vlanid is not None else '',
                    bond if bond is not None else '',
                    interface if interface is not None else '',
                ] +
                parameters
            ),
        )

    def _setIncomplete(self, msg):
        self.environment[
            odeploycons.CoreEnv.INSTALL_INCOMPLETE
        ] = True
        self.environment[
            odeploycons.CoreEnv.INSTALL_INCOMPLETE_REASONS
        ].append(msg)
        self.logger.warning(msg)

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.VdsmEnv.MANAGEMENT_BRIDGE_NAME,
            None
        )
        self.environment.setdefault(odeploycons.VdsmEnv.ENGINE_HOST, None)
        self.environment.setdefault(odeploycons.VdsmEnv.ENGINE_ADDRESS, None)
        self.environment.setdefault(odeploycons.VdsmEnv.ENGINE_PORT, 80)
        self.environment.setdefault(odeploycons.VdsmEnv.CONNECTION_TIMEOUT, 10)
        self.environment.setdefault(odeploycons.VdsmEnv.CONNECTION_RETRIES, 60)
        self.command.detect('ip')
        self.command.detect('nmcli')

    @plugin.event(
        stage=plugin.Stages.STAGE_INTERNAL_PACKAGES,
    )
    def _internal_packages(self):
        self.packager.install(packages=['iproute'])

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=(
            lambda self: (
                self.environment[
                    odeploycons.VdsmEnv.MANAGEMENT_BRIDGE_NAME
                ] is not None
            )
        ),
    )
    def _validation(self):
        """Resolve engine host name now as we won't be able
        to do so during the blackout.

        """
        host = self.environment[odeploycons.VdsmEnv.ENGINE_HOST]

        if host is None:
            raise RuntimeError(
                _(
                    'Bridge creation requested but engine host '
                    'was not specified'
                )
            )

        if self._interfaceExists(
            self.environment[odeploycons.VdsmEnv.MANAGEMENT_BRIDGE_NAME]
        ):
            self.logger.debug('Management interface already exists')
        else:
            try:
                addresses = set([
                    address[0] for __, __, __, __, address in
                    socket.getaddrinfo(
                        host,
                        None
                    )
                ])
                self.logger.debug('Engine %s addresses: %s', host, addresses)
            except:
                self.logger.debug(
                    "Cannot resolve engine '%s'",
                    host,
                    exc_info=True
                )
                raise RuntimeError(
                    _("Cannot resolve engine host name '{host}'").format(
                        host=host
                    )
                )

            engineAddress = None
            for address in addresses:
                try:
                    self._waitForRoute(
                        host=(
                            address,
                            int(
                                self.environment[
                                    odeploycons.VdsmEnv.ENGINE_PORT
                                ]
                            ),
                        ),
                        timeout=self.environment[
                            odeploycons.VdsmEnv.CONNECTION_TIMEOUT
                        ],
                        retries=2,
                    )
                    engineAddress = address
                    break
                except:
                    self.logger.debug('connection exception', exc_info=True)

            if engineAddress is None:
                raise RuntimeError(
                    _(
                        "Cannot connect engine host '{name}' "
                        "at any of the addresses {addresses}'"
                    ).format(
                        name=host,
                        addresses=addresses,
                    )
                )

            self.environment[
                odeploycons.VdsmEnv.ENGINE_ADDRESS
            ] = engineAddress

            install = True
            interface = self._getInterfaceToInstallBasedOnDestination(
                address=engineAddress
            )
            if self._interfaceIsBridge(name=interface):
                #
                # only for ovirt-node we delete existing
                # bridge?
                #
                if self.environment[odeploycons.VdsmEnv.OVIRT_NODE]:
                    if not interface.startswith('br'):
                        self._setIncomplete(
                            _(
                                'Non standard bridge name {interface} '
                                'while running on hypervisor '
                                'br prefix expected. '
                                'Please configure manually '
                                'bridge on this device with name {bridge}'
                            ).format(
                                interface=interface,
                                bridge=self.environment[
                                    odeploycons.VdsmEnv.MANAGEMENT_BRIDGE_NAME
                                ],
                            )
                        )
                        install = False
                    else:
                        nic = interface.replace('br', '', 1)
                        if nic not in self._interfacesOfBridge(name=interface):
                            self._setIncomplete(
                                _(
                                    'non standard bridge name {interface} '
                                    'while running on hypervisor '
                                    'name does not match any physical '
                                    'interface. '
                                    'Please configure manually '
                                    'bridge on this device with name {bridge}'
                                ).format(
                                    interface=interface,
                                    bridge=self.environment[
                                        odeploycons.VdsmEnv.
                                        MANAGEMENT_BRIDGE_NAME
                                    ],
                                )
                            )
                            install = False
                        else:
                            # continue validation based on nic
                            interface = nic
                else:
                    self.logger.info(
                        _(
                            'Management channel interface {interface} '
                            'is already a bridge'
                        ).format(
                            interface=interface,
                        )
                    )
                    install = False

            if install:
                # this is here to raise exception
                # if any error we stop before performing change
                self._getVlanMasterDevice(name=interface)

                self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _misc(self):
        if self.services.exists('libvirtd'):
            if not self.services.supportsDependency:
                self.services.state('messagebus', True)
            self.services.state('libvirtd', True)

        interface = self._getInterfaceToInstallBasedOnDestination(
            address=self.environment[odeploycons.VdsmEnv.ENGINE_ADDRESS]
        )
        parameters = self._rhel_getInterfaceConfigParameters(name=interface)

        # The followin can be executed
        # only at node as we won't reach here
        # if we are not running on node
        if (
            self.environment[odeploycons.VdsmEnv.OVIRT_NODE] and
            self._interfaceIsBridge(name=interface)
        ):
            nic = interface.replace('br', '', 1)
            self._removeBridge(
                name=interface,
                interface=nic,
            )
            interface = nic

        self._createBridge(
            name=self.environment[odeploycons.VdsmEnv.MANAGEMENT_BRIDGE_NAME],
            interface=interface,
            parameters=parameters,
        )

        self._waitForRoute(
            host=(
                self.environment[odeploycons.VdsmEnv.ENGINE_ADDRESS],
                int(self.environment[odeploycons.VdsmEnv.ENGINE_PORT])
            ),
            timeout=self.environment[odeploycons.VdsmEnv.CONNECTION_TIMEOUT],
            retries=self.environment[odeploycons.VdsmEnv.CONNECTION_RETRIES],
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_TRANSACTION_END,
        condition=lambda self: self._enabled,
    )
    def _transaction_end(self):
        self.execute(
            (
                os.path.join(
                    odeploycons.FileLocations.VDSM_DATA_DIR,
                    'vdsm-store-net-config',
                ),
            ),
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self._enabled,
    )
    def _closeup(self):
        self.services.startup('network', True)


# vim: expandtab tabstop=4 shiftwidth=4
