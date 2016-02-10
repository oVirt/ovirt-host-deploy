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


"""vdsm configuration management."""


import configparser
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
    """vdsm configuration management."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.environment.setdefault(
            odeploycons.VdsmEnv.CONFIG_OVERRIDE,
            True
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.CONFIG_OVERRIDE
        ],
    )
    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.OVIRT_VINTAGE_NODE
        ],
    )
    def _validation(self):
        config = configparser.ConfigParser()
        config.optionxform = str

        vars = [
            var for var in self.environment
            if var.startswith(odeploycons.VdsmEnv.CONFIG_PREFIX)
        ]

        for var in vars:
            try:
                section, key = var.replace(
                    odeploycons.VdsmEnv.CONFIG_PREFIX, ''
                ).split('/', 1)
            except ValueError:
                raise RuntimeError(
                    _('Invalid VDSM configuration entry {key}').format(
                        key=key
                    )
                )

            value = self.environment[var]

            if not config.has_section(section):
                config.add_section(section)
            config.set(section, key, value)

        class buf(object):
            """io.StringIO is not working???"""
            def __init__(self):
                self.content = ''

            def write(self, s):
                self.content += s
        b = buf()
        config.write(b)

        if b.content:
            self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=odeploycons.FileLocations.VDSM_CONFIG_FILE,
                    owner='root',
                    enforcePermissions=True,
                    content=b.content,
                    modifiedList=self.environment[
                        otopicons.CoreEnv.MODIFIED_FILES
                    ],
                )
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.OVIRT_VINTAGE_NODE
        ],
    )
    def _closeup(self):
        if self.services.exists('vdsm-reg'):
            self.services.state('vdsm-reg', False)


# vim: expandtab tabstop=4 shiftwidth=4
