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


"""ovirt-node detection."""


import os
import re
import glob
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import util
from otopi import plugin


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """ovirt-node detection.

    Environment:
        VdsmEnv.OVIRT_NODE -- is node.
        VdsmEnv.NODE_PLUGIN_VDSM_VERSION -- version of ovirt-node-plugin-vdsm

    """

    _PLUGIN_VER_FILE_RE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            (?P<key>[a-zA-Z0-9_]+)
            =
            (?P<value>.*)
            $
        """,
    )

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    def _get_node_plugin_version(self, plugin_name):
        result = None
        version_file = '/etc/default/version%s' % (
            '.%s' % plugin_name if plugin_name else ''
        )
        if os.path.exists(version_file):
            content = {}
            with open(version_file) as f:
                for line in f.read().splitlines():
                    m = self._PLUGIN_VER_FILE_RE.match(line)
                    if m is not None:
                        content[m.group('key')] = m.group('value')
            result = (
                content.get('VERSION', None),
                content.get('RELEASE', None),
            )

        self.logger.debug(
            "Plugin '%s' version: '%s'",
            plugin_name,
            result,
        )

        return result

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_FIRST,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.VdsmEnv.OVIRT_NODE,
            (
                os.path.exists('/etc/rhev-hypervisor-release') or
                bool(glob.glob('/etc/ovirt-node-*-release'))
            )
        )
        self.environment[
            odeploycons.VdsmEnv.OVIRT_NODE_HAS_OWN_BRIDGES
        ] = len(glob.glob('/sys/class/net/br*/bridge/bridge_id')) != 0
        self.environment.setdefault(
            odeploycons.CoreEnv.OFFLINE_PACKAGER,
            self.environment[
                odeploycons.VdsmEnv.OVIRT_NODE
            ]
        )

        if self.environment[odeploycons.VdsmEnv.OVIRT_NODE]:
            self.environment[
                odeploycons.VdsmEnv.NODE_PLUGIN_VDSM_VERSION
            ] = self._get_node_plugin_version(
                'ovirt-node-plugin-vdsm'
            )


# vim: expandtab tabstop=4 shiftwidth=4
