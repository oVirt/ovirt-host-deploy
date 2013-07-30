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


"""neutron plugin."""


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import util
from otopi import plugin


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """neutron.

    Environment:
        OpenStackEnv.NEUTRON_ENABLE -- perform neutron installation.
        OpenStackEnv.NEUTRON_CONFIG_PREFIX -- neutron configuration.

    TODO:
        drop the use of openstack-config and update files directly
        so we can rollback and backup.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.OpenStackEnv.NEUTRON_ENABLE,
            False
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('openstack-config')

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.OpenStackEnv.NEUTRON_ENABLE
        ],
    )
    def _validation(self):
        self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        self.packager.installUpdate(('openstack-quantum',))

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _misc(self):
        vars = [
            var for var in self.environment
            if var.startswith(odeploycons.OpenStackEnv.NEUTRON_CONFIG_PREFIX)
        ]

        for var in vars:
            try:
                section, key = var.replace(
                    odeploycons.OpenStackEnv.NEUTRON_CONFIG_PREFIX, ''
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
                    odeploycons.FileLocations.OPENSTACK_NEUTRON_CONFIG,
                    section,
                    key,
                    str(value),
                ),
            )


# vim: expandtab tabstop=4 shiftwidth=4
