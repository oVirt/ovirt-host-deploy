#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2012 Red Hat, Inc.
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


"""Fake packager for ovirt-node"""


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import packager
from otopi import util
from otopi import plugin


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase, packager.PackagerBase):
    """Offline packager."""
    def install(self, packages, ignoreErrors=False):
        pass

    def update(self, packages, ignoreErrors=False):
        pass

    def queryPackages(self, patterns=None):
        if patterns == ['vdsm']:
            return [
                {
                    'operation': 'installed',
                    'display_name': 'vdsm',
                    'name': 'vdsm',
                    'version': '999.9.9',
                    'release': '1',
                    'epoch': '0',
                    'arch': 'noarch',
                },
            ]
        else:
            return []

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_MEDIUM,
    )
    def _init(self):
        if self.environment.setdefault(
            odeploycons.CoreEnv.OFFLINE_PACKAGER,
            False
        ):
            self.logger.debug('Registering offline packager')
            self.context.registerPackager(packager=self)


# vim: expandtab tabstop=4 shiftwidth=4
