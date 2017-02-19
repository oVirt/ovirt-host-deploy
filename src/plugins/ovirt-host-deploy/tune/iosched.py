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


from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """iosched setup plugin."""

    # In previous versions, we used to write this file to change the
    # default scheduler to 'deadline'. This is not needed anymore,
    # because this is the default for supported kernels, and we want
    # to remove this file, because its content made overriding the
    # scheduler harder than necessary.
    DEST_UDEV_RULE_FILE = '/etc/udev/rules.d/12-ovirt-iosched.rules'

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('udevadm')

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
    )
    def _remove_old_iosched_udev_conf(self):
        removed = False
        if os.path.exists(self.DEST_UDEV_RULE_FILE):
            try:
                os.unlink(self.DEST_UDEV_RULE_FILE)
                removed = True
            except OSError:
                self.logger.warning(
                    _("Cannot remove file '{name}'.").format(
                        name=self.DEST_UDEV_RULE_FILE,
                    )
                )
                self.logger.debug(exc_info=True)
        if removed and not self.environment[odeploycons.CoreEnv.FORCE_REBOOT]:
            self.execute(
                [
                    self.command.get('udevadm'),
                    'control',
                    '--reload',
                ],
                raiseOnError=False,
            )
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
