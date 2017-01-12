#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2015 Red Hat, Inc.
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


"""oVirt Hosted Engine configuration plugin."""


import gettext
import os

from otopi import constants as otopicons
from otopi import filetransaction
from otopi import plugin
from otopi import transaction
from otopi import util


from ovirt_host_deploy import constants as odeploycons

ha_client = None
try:
    import ovirt_hosted_engine_ha.client.client as ha_client
except ImportError:
    pass


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """oVirt Hosted Engine configuration plugin."""

    class HeMaintenanceModeTransaction(transaction.TransactionElement):
        """transaction element for setting he maintenance mode."""

        def __init__(self, parent):
            self._parent = parent

        def __str__(self):
            return _("HeMaintenanceMode Transaction")

        def prepare(self):
            pass

        def abort(self):
            try:
                ha_client.HAClient().set_maintenance_mode(
                    ha_client.HAClient.MaintenanceMode.LOCAL, True
                )
            except Exception:
                self._parent.logger.error(
                    _('Error setting HA local maintenance mode to true')
                )

        def commit(self):
            try:
                ha_client.HAClient().set_maintenance_mode(
                    ha_client.HAClient.MaintenanceMode.LOCAL, False
                )
            except Exception:
                self._parent.logger.error(
                    _('Error setting HA local maintenance mode to false')
                )

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: (
            self.environment[
                odeploycons.HostedEngineEnv.ACTION
            ] == odeploycons.Const.HOSTED_ENGINE_ACTION_REMOVE and
            os.path.exists(odeploycons.FileLocations.HOSTED_ENGINE_CONF)
        )
    )
    def _clear_ha_conf(self):
        self.logger.info(_('Removing hosted-engine configuration'))
        self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
            filetransaction.FileTransaction(
                name=odeploycons.FileLocations.HOSTED_ENGINE_CONF,
                content='',
                modifiedList=self.environment[
                    otopicons.CoreEnv.MODIFIED_FILES
                ],
            ),
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self.environment[
            odeploycons.HostedEngineEnv.ACTION
        ] == odeploycons.Const.HOSTED_ENGINE_ACTION_DEPLOY,
    )
    def _set_ha_conf(self):
        self.logger.info(_('Updating hosted-engine configuration'))
        content = (
            'ca_cert={ca_cert}\n'
        ).format(
            ca_cert=os.path.join(
                odeploycons.FileLocations.VDSM_TRUST_STORE,
                odeploycons.FileLocations.VDSM_SPICE_CA_FILE
            ),
        )
        for env_key in self.environment:
            if env_key.startswith(
                odeploycons.HostedEngineEnv.HOSTED_ENGINE_CONFIG_PREFIX
            ):
                key = env_key.replace(
                    odeploycons.HostedEngineEnv.
                    HOSTED_ENGINE_CONFIG_PREFIX,
                    ''
                )
                content += '{key}={value}\n'.format(
                    key=key,
                    value=self.environment[env_key],
                )
        self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
            filetransaction.FileTransaction(
                name=odeploycons.FileLocations.HOSTED_ENGINE_CONF,
                content=content,
                modifiedList=self.environment[
                    otopicons.CoreEnv.MODIFIED_FILES
                ],
            ),
        )
        if ha_client is None:
            self.logger.error(_('HA client was not imported'))
        else:
            self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                self.HeMaintenanceModeTransaction(
                    parent=self,
                )
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self.environment[
            odeploycons.HostedEngineEnv.ACTION
        ] == odeploycons.Const.HOSTED_ENGINE_ACTION_REMOVE,
    )
    def _remove_conf(self):
        if os.path.exists(odeploycons.FileLocations.HOSTED_ENGINE_CONF):
            os.unlink(odeploycons.FileLocations.HOSTED_ENGINE_CONF)


# vim: expandtab tabstop=4 shiftwidth=4
