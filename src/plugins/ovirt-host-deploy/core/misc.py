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


"""Misc plugin."""


import gettext
import os


from otopi import constants as otopicons
from otopi import context
from otopi import plugin
from otopi import util


from ovirt_host_deploy import config
from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """Misc plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_BOOT,
        before=(
            otopicons.Stages.CORE_LOG_INIT,
        ),
        priority=plugin.Stages.PRIORITY_HIGH - 10,
    )
    def _preinit(self):
        self.environment.setdefault(
            otopicons.CoreEnv.LOG_FILE_NAME_PREFIX,
            odeploycons.FileLocations.OVIRT_HOST_DEPLOY_LOG_PREFIX
        )
        self.environment.setdefault(
            otopicons.CoreEnv.CONFIG_FILE_NAME,
            self.resolveFile(
                os.environ.get(
                    otopicons.SystemEnvironment.CONFIG,
                    self.resolveFile(
                        odeploycons.FileLocations.OVIRT_HOST_DEPLOY_CONFIG_FILE
                    )
                )
            )
        )
        self.environment[
            odeploycons.CoreEnv.INTERFACE_VERSION
        ] = config.INTERFACE_VERSION

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_FIRST,
    )
    def _confirm(self):
        if not self.dialog.confirm(
            name=odeploycons.Confirms.DEPLOY_PROCEED,
            description='Proceed with ovirt-host-deploy',
            note=_(
                'Continuing will configure this host for serving '
                'as hypervisor. Are you sure you want to continue? (yes/no) '
            ),
            prompt=True,
        ):
            raise context.Abort('Aborted by user')

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.CoreEnv.FORCE_REBOOT,
            False
        )

        self.logger.debug(
            'ovirt-host-deploy interface version %s' % (
                config.INTERFACE_VERSION
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _setup(self):
        self.dialog.note(
            text=_('Version: {package}-{version} ({local_version})').format(
                package=config.PACKAGE_NAME,
                version=config.PACKAGE_VERSION,
                local_version=config.LOCAL_VERSION,
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: (
            self.environment[
                odeploycons.CoreEnv.FORCE_REBOOT
            ] and
            not self.environment[
                odeploycons.CoreEnv.INSTALL_INCOMPLETE
            ]
        ),
    )
    def _closeup(self):
        self.environment[otopicons.SysEnv.REBOOT] = True


# vim: expandtab tabstop=4 shiftwidth=4
