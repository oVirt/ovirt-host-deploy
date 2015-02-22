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


"""ioscehd setup plugin."""


import gettext


import os


from otopi import constants as otopicons
from otopi import filetransaction
from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """iosched setup plugin."""

    DEST_UDEV_RULE_FILE = '/etc/udev/rules.d/12-ovirt-iosched.rules'
    SRC_UDEV_RULE_FILE = 'ovirt-iosched.rules'

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('udevadm')

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
    )
    def _misc(self):
        with open(
            os.path.join(
                os.path.dirname(__file__),
                self.SRC_UDEV_RULE_FILE,
            ),
            'r'
        ) as f:
            self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=self.DEST_UDEV_RULE_FILE,
                    content=f.read(),
                    modifiedList=self.environment[
                        otopicons.CoreEnv.MODIFIED_FILES
                    ],
                )
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        priority=plugin.Stages.PRIORITY_LOW,
        condition=lambda self: not self.environment[
            odeploycons.CoreEnv.FORCE_REBOOT
        ],
    )
    def _refresh(self):
        self.execute(
            [
                self.command.get('udevadm'),
                'trigger',
                '--type=devices',
                '--action=change',
            ],
            raiseOnError=False,
        )


# vim: expandtab tabstop=4 shiftwidth=4
