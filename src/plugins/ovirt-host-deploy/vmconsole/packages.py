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


"""Serial console PKI artifacts."""


import gettext


from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self._enabled = False
        self.environment.setdefault(
            odeploycons.VMConsoleEnv.ENABLE,
            False
        )
        self.environment.setdefault(
            odeploycons.VMConsoleEnv.SUPPORT,
            odeploycons.Const.VMCONSOLE_SUPPORT_NONE
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _customization(self):
        if self.packager.queryPackages(
            patterns=('ovirt-vmconsole-host',),
        ):
            self.environment[
                odeploycons.VMConsoleEnv.SUPPORT
            ] = odeploycons.Const.VMCONSOLE_SUPPORT_V1

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.VMConsoleEnv.ENABLE
        ]
    )
    def _validation(self):
        self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        self.packager.installUpdate(('ovirt-vmconsole-host',))

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        priority=plugin.Stages.PRIORITY_LOW,
        condition=lambda self: self._enabled,
    )
    def _start(self):
        self.logger.info(_('Starting ovirt-vmconsole-host-sshd'))
        if self.services.exists('ovirt-vmconsole-host-sshd'):
            self.services.state('ovirt-vmconsole-host-sshd', False)
            self.services.state('ovirt-vmconsole-host-sshd', True)


# vim: expandtab tabstop=4 shiftwidth=4
