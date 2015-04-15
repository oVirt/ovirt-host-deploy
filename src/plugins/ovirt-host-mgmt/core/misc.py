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


"""Misc plugin."""


import gettext
import os


from otopi import constants as otopicons
from otopi import plugin
from otopi import util


from ovirt_host_mgmt import config
from ovirt_host_mgmt import constants as omgmt


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
            otopicons.Stages.CORE_CONFIG_INIT,
        ),
    )
    def _preinit(self):
        self.environment.setdefault(
            otopicons.CoreEnv.LOG_FILE_NAME_PREFIX,
            omgmt.FileLocations.OVIRT_HOST_MGMT_LOG_PREFIX
        )
        self.environment.setdefault(
            otopicons.CoreEnv.CONFIG_FILE_NAME,
            self.resolveFile(
                os.environ.get(
                    otopicons.SystemEnvironment.CONFIG,
                    self.resolveFile(
                        omgmt.FileLocations.OVIRT_HOST_MGMT_CONFIG_FILE
                    )
                )
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


# vim: expandtab tabstop=4 shiftwidth=4
