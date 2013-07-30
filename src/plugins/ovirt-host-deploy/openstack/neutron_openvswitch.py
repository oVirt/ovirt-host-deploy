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


"""neutron openvswitch plugin."""


import os
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import util
from otopi import plugin


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """neutron openvswitch.

    Environment:
        OpenStackEnv.NEUTRON_OPENVSWITCH_ENABLE --
            perform neutron openvswitch plugin installation.
        OpenStackEnv.NEUTRON_OPENVSWITCH_INTERNAL_BRIDGE --
            internal bridge name.
        OpenStackEnv.NEUTRON_LINUXBRODGE_CONFIG_PREFIX --
            neutron openvswitch configuration.

    TODO:
        drop the use of openstack-config and update files directly
        so we can rollback and backup.

    """

    def _createBridge(self, name):
        rc, stdout, stderr = self.execute(
            args=(
                self.command.get('ovs-vsctl'),
                'br-exists',
                name,
            ),
            raiseOnError=False,
        )
        if rc == 0:
            # we already have this bridge
            pass
        elif rc == 2:
            # we do not have this bridge
            self.execute(
                (
                    self.command.get('ovs-vsctl'),
                    'add-br',
                    name,
                ),
            )
        else:
            raise RuntimeError(_('Invalid response from OVS'))

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.OpenStackEnv.NEUTRON_OPENVSWITCH_ENABLE,
            False
        )
        self.environment.setdefault(
            odeploycons.OpenStackEnv.NEUTRON_OPENVSWITCH_INTERNAL_BRIDGE,
            'br-int'
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('openstack-config')
        self.command.detect('ovs-vsctl')

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.OpenStackEnv.NEUTRON_OPENVSWITCH_ENABLE
        ],
    )
    def _validation(self):
        self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        self.packager.installUpdate(
            (
                'openstack-quantum-openvswitch',
                'vdsm-hook-openstacknet',
            ),
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _misc(self):
        vars = [
            var for var in self.environment
            if var.startswith(
                odeploycons.OpenStackEnv.
                NEUTRON_OPENVSWITCH_CONFIG_PREFIX
            )
        ]

        for var in vars:
            try:
                section, key = var.replace(
                    odeploycons.OpenStackEnv.NEUTRON_OPENVSWITCH_CONFIG_PREFIX,
                    ''
                ).split('/', 1)
            except ValueError:
                raise RuntimeError(
                    _('Invalid neutron configuration entry {key}').format(
                        key=key
                    )
                )

            value = self.environment[var]

            self.execute(
                (
                    self.command.get('openstack-config'),
                    '--set',
                    (
                        odeploycons.FileLocations.
                        OPENSTACK_NEUTRON_OPENVSWITCH_CONFIG
                    ),
                    section,
                    key,
                    str(value),
                ),
            )
        if os.path.exists(
            odeploycons.FileLocations.OPENSTACK_NEUTRON_PLUGIN_CONFIG
        ):
            os.unlink(
                odeploycons.FileLocations.OPENSTACK_NEUTRON_PLUGIN_CONFIG
            )
        os.symlink(
            odeploycons.FileLocations.OPENSTACK_NEUTRON_OPENVSWITCH_CONFIG,
            odeploycons.FileLocations.OPENSTACK_NEUTRON_PLUGIN_CONFIG
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _bridge(self):
        self.services.state('openvswitch', True)
        self._createBridge(
            name=self.environment[
                odeploycons.OpenStackEnv.
                NEUTRON_OPENVSWITCH_INTERNAL_BRIDGE
            ],
        )
        for setting in self.environment.get(
            odeploycons.OpenStackEnv.NEUTRON_OPENVSWITCH_CONFIG_PREFIX +
            'OVS/bridge_mappings',
            ''
        ).split(','):
            setting = setting.strip()
            bridge = setting.split(':')[1]
            self._createBridge(
                name=bridge,
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: (
            self._enabled and
            not self.environment[
                odeploycons.CoreEnv.FORCE_REBOOT
            ]
        ),
    )
    def _closeup(self):
        self.logger.info(_('Starting neutron openvswitch plugin'))
        for state in (False, True):
            self.services.state('quantum-openvswitch-agent', state)
        self.services.startup('quantum-openvswitch-agent', True)
        self.services.startup('quantum-ovs-cleanup', True)
        self.services.startup('openvswitch', True)


# vim: expandtab tabstop=4 shiftwidth=4
