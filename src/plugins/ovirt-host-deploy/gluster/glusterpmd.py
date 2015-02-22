#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2012-2014 Red Hat, Inc.
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


"""glusterpmd plugin."""


import gettext


from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """glusterpmd plugin"""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: (
            self.environment[
                odeploycons.GlusterEnv.MONITORING_ENABLE
            ] and
            self.environment[
                odeploycons.GlusterEnv.ENABLE
            ]
        )
    )
    def _closeup(self):
        if self.services.exists('glusterpmd'):
            self.logger.info(_('Starting glusterpmd service'))
            self.services.state('glusterpmd', True)
            self.services.startup('glusterpmd', True)


# vim: expandtab tabstop=4 shiftwidth=4
