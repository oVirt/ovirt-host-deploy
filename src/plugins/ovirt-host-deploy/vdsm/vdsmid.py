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


"""vdsm identification plugin."""


import os
import platform
import uuid
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import constants as otopicons
from otopi import util
from otopi import plugin
from otopi import filetransaction


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """vdsm identification.

    Environment:
        VdsmEnv.VDSM_ID -- vdsm id.

    Reads id from file.
    If not exists tries to use dmidecode.
    If hardware uuid not available generate own.
    Store id in file.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._vdsmId = None

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(odeploycons.VdsmEnv.VDSM_ID, None)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('dmidecode')
        if os.path.exists(odeploycons.FileLocations.VDSM_ID_FILE):
            with open(odeploycons.FileLocations.VDSM_ID_FILE, 'r') as f:
                self._vdsmId = f.readline().rstrip('\n')
            self.environment[odeploycons.VdsmEnv.VDSM_ID] = self._vdsmId

    @plugin.event(
        stage=plugin.Stages.STAGE_INTERNAL_PACKAGES,
        condition=(
            lambda self: self.environment[odeploycons.VdsmEnv.VDSM_ID] is None
        ),
    )
    def _packages(self):
        if platform.machine() in ('x86_64', 'i686'):
            self.packager.install(('dmidecode',))

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        priority=plugin.Stages.PRIORITY_HIGH,
        condition=(
            lambda self: self.environment[odeploycons.VdsmEnv.VDSM_ID] is None
        ),
    )
    def _detect_id(self):
        vdsmId = None

        arch = platform.machine()
        if arch in ('x86_64', 'i686'):
            (rc, stdout, stderr) = self.execute(
                (
                    self.command.get('dmidecode'),
                    '-s',
                    'system-uuid'
                ),
                raiseOnError=False
            )
            if rc != 0 or len(stdout) != 1:
                self.logger.warning(_('Invalid dmidecode output'))
            elif stdout[0].startswith('Not '):
                self.logger.warning(_('No system uuid'))
            else:
                vdsmId = stdout[0]
        elif arch in ('ppc', 'ppc64'):
            #eg. output IBM,03061C14A
            if os.path.exists('/proc/device-tree/system-id'):
                with open('/proc/device-tree/system-id') as f:
                    vdsmId = f.readline().replace(',', '')

        if vdsmId is None:
            vdsmId = str(uuid.uuid4())

        self.environment[odeploycons.VdsmEnv.VDSM_ID] = vdsmId

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=(
            lambda self: self._vdsmId != self.environment[
                odeploycons.VdsmEnv.VDSM_ID
            ]
        ),
    )
    def _store_id(self):
        self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
            filetransaction.FileTransaction(
                name=odeploycons.FileLocations.VDSM_ID_FILE,
                owner='root',
                enforcePermissions=True,
                content=self.environment[
                    odeploycons.VdsmEnv.VDSM_ID
                ],
                modifiedList=self.environment[
                    otopicons.CoreEnv.MODIFIED_FILES
                ],
            )
        )


# vim: expandtab tabstop=4 shiftwidth=4
