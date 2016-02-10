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


"""tuned configuration plugin."""


import gettext


from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """tuned configuration plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = False
        self._profile = None

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
        condition=lambda self: (
            not self.environment[
                odeploycons.VdsmEnv.OVIRT_VINTAGE_NODE
            ]
        ),
    )
    def _setup(self):
        self.command.detect('tuned-adm')
        self._enabled = True
        self.environment.setdefault(
            odeploycons.TuneEnv.TUNED_PROFILE,
            None
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self._enabled,
    )
    def _validation(self):
        self._profile = self.environment[odeploycons.TuneEnv.TUNED_PROFILE]

        if self._profile is None:
            if self.environment[odeploycons.GlusterEnv.ENABLE]:
                self._profile = 'rhs-virtualization'
            else:
                self._profile = 'virtual-host'

        self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        self.packager.installUpdate(('tuned',))

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _misc(self):
        # tuned-adm does not work if daemon is down!
        self.services.state('tuned', True)
        rc, stdout, stderr = self.execute(
            (
                self.command.get('tuned-adm'),
                'profile',
                self._profile,
            ),
            raiseOnError=False,
        )
        if rc != 0:
            self.logger.warning(_('Cannot set tuned profile'))
        else:
            self.services.startup('tuned', True)


# vim: expandtab tabstop=4 shiftwidth=4
