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


"""metrics configuration plugin."""


import gettext


from otopi import constants as otopicons
from otopi import filetransaction
from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """vdsm metrics conf.

    Environment:
        VDSM/enableMetricsConfig - whether to write it or not
        VDSM/metricsConfig - content
    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.VdsmEnv.ENABLE_METRICS_CONFIG,
            True
        )
        self.environment.setdefault(
            odeploycons.VdsmEnv.METRICS_CONFIG,
            (
                '[metrics]\n'
                '# Enable metric collector (default: false)\n'
                'enabled = true\n'
                '\n'
                '# Address to remote metric collector (default: localhost)\n'
                'collector_address = localhost\n'
                '\n'
                '# Type of metric collector (supporting: stastd, hawkular)\n'
                'collector_type = statsd\n'
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.ENABLE_METRICS_CONFIG
        ],
    )
    def _config_vdsm_metrics(self):
        self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
            filetransaction.FileTransaction(
                name=odeploycons.FileLocations.VDSM_METRICS_CONF,
                owner='root',
                enforcePermissions=True,
                content=self.environment[
                    odeploycons.VdsmEnv.METRICS_CONFIG
                ],
                modifiedList=self.environment[
                    otopicons.CoreEnv.MODIFIED_FILES
                ],
            )
        )


# vim: expandtab tabstop=4 shiftwidth=4
