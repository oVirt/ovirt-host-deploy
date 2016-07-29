#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2015 Red Hat, Inc.
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


"""oVirt Hosted Engine packages plugin."""


import gettext
import platform


from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """oVirt Hosted Engine pacakges.

    Environment:
        HostedEngineEnv.ACTION -- perform Hosted Engine customization:
          Const.HOSTED_ENGINE_ACTION_NONE: do nothing
          Const.HOSTED_ENGINE_ACTION_DEPLOY: deploy configuration
          Const.HOSTED_ENGINE_ACTION_REMOVE: remove configuration
    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.HostedEngineEnv.ACTION,
            odeploycons.Const.HOSTED_ENGINE_ACTION_NONE
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.HostedEngineEnv.ACTION
        ] == odeploycons.Const.HOSTED_ENGINE_ACTION_DEPLOY,
    )
    def _validation(self):
        if platform.machine() != 'x86_64':
            self.logger.error(
                _(
                    'Hosted Engine support requested on unsupported '
                    'machine: {arch}. Disabling'
                ).format(arch=platform.machine())
            )
            self.environment[
                odeploycons.HostedEngineEnv.ACTION
            ] = odeploycons.Const.HOSTED_ENGINE_ACTION_NONE

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self.environment[
            odeploycons.HostedEngineEnv.ACTION
        ] == odeploycons.Const.HOSTED_ENGINE_ACTION_DEPLOY,
    )
    def _packages(self):
        for s in ('ovirt-ha-agent', 'ovirt-ha-broker'):
            if self.services.exists(s):
                self.services.state(s, False)
        self.packager.installUpdate(('ovirt-hosted-engine-setup',))

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self.environment[
            odeploycons.HostedEngineEnv.ACTION
        ] != odeploycons.Const.HOSTED_ENGINE_ACTION_NONE,
        after=(
            odeploycons.Stages.VDSM_STARTED,
        ),
        priority=plugin.Stages.PRIORITY_LOW,
    )
    def _closeup(self):
        self.logger.info(_('Starting ovirt-ha-agent'))
        self.services.startup(
            name='ovirt-ha-agent',
            state=(
                self.environment[
                    odeploycons.HostedEngineEnv.ACTION
                ] == odeploycons.Const.HOSTED_ENGINE_ACTION_DEPLOY
            ),
        )
        self.services.state(
            name='ovirt-ha-agent',
            state=False,
        )
        if self.environment[
            odeploycons.HostedEngineEnv.ACTION
        ] == odeploycons.Const.HOSTED_ENGINE_ACTION_DEPLOY:
            self.services.state(
                name='ovirt-ha-agent',
                state=True,
            )


# vim: expandtab tabstop=4 shiftwidth=4
