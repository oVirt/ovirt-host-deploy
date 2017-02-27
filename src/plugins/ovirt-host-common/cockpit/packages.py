#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2017 Red Hat, Inc.
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


"""Cockpit packages plugin."""


import gettext
import platform


from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """Cockpit packages plugins"""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self.enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
    )
    def _validation(self):
        if platform.machine() != 'x86_64':
            self.logger.error(
                _(
                    'Cockpit support not available on unsupported '
                    'machine: {arch}. Disabling'
                ).format(arch=platform.machine())
            )
            self.enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self.enabled,
    )
    def _packages(self):
        self.packager.installUpdate(('cockpit-ovirt-dashboard',))

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self.enabled,
    )
    def _closeup(self):
        self.logger.info(_('Starting cockpit'))
        self.services.state('cockpit', True)
        self.services.startup('cockpit', True)


# vim: expandtab tabstop=4 shiftwidth=4
