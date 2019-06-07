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


import codecs
import configparser
import gettext
import io
import os
import re

from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """ovirt-node detection.

    Environment:
        VdsmEnv.OVIRT_CONTAINER_NODE -- is container node.
        VdsmEnv.OVIRT_NODE -- is oVirt Node or derivate
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

    def hasconf(self, filename, key, value):
        if os.path.exists(filename):
            with codecs.open(filename, 'r', encoding='utf-8') as f:
                parser = configparser.ConfigParser()
                parser.readfp(
                    io.StringIO('[default]\n' + f.read())
                )
                try:
                    val = parser.get('default', key)
                    if val == value or val == '"%s"' % value:
                        return True
                    else:
                        return False
                except configparser.Error:
                    return False
        else:
            return False

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
        priority=plugin.Stages.PRIORITY_FIRST,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.VdsmEnv.OVIRT_CONTAINER_NODE,
            (
                os.path.exists('/etc/rhev-container-hypervisor-release') or
                os.path.exists('/etc/ovirt-container-node-release')
            )
        )
        self.environment.setdefault(
            odeploycons.VdsmEnv.OVIRT_NODE,
            (
                self.hasconf(odeploycons.FileLocations.OVIRT_NODE_OS_FILE,
                             odeploycons.FileLocations.OVIRT_NODE_VARIANT_KEY,
                             odeploycons.FileLocations.OVIRT_NODE_VARIANT_VAL)
            )
        )

# vim: expandtab tabstop=4 shiftwidth=4
