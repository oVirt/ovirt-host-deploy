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


"""gluster nrpe plugin."""

import gettext
import os
import re


from otopi import constants as otopicons
from otopi import filetransaction
from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """
    Environment:
        GlusterEnv.MONITORING_ENABLE -- enable gluster nrpe agent

        GlusterEnv.MONITORING_SERVER -- server accessing nrpe agent

    Configuration:
    # sample nrpe config file format
    # comment
    key1=value1
    key2=value2 # comment
    key3=
    key4= #comment
    #key5=value5
    allowed_hosts=
    allowed_hosts=a,b,c
    allowed_hosts=d,a,b,c
    """
    _RE_KEY_VALUE = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            \s*
            (?P<key>\w+)
            \s*
            =
            \s*
            (?P<value>[^#]*)
            ([#].*)?
            $
        """,
    )

    def _getNewFileContent(self, content, server):
        newcontent = []
        for line in content:
            m = self._RE_KEY_VALUE.match(line)
            if m is not None and m.group('key') == 'allowed_hosts':
                s = set(
                    [
                        e.strip() for e in m.group('value').split(',')
                        if e.strip()
                    ]
                )
                if server not in s:
                    s.add(server)
                    line = 'allowed_hosts=%s' % ','.join(sorted(s))
            newcontent.append(line)
        return newcontent

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._modified = False

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _setup(self):
        self.environment.setdefault(
            odeploycons.GlusterEnv.MONITORING_ENABLE,
            False
        )
        self.environment.setdefault(
            odeploycons.GlusterEnv.MONITORING_SERVER,
            None
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: (
            self.environment[
                odeploycons.GlusterEnv.MONITORING_ENABLE
            ] and
            self.environment[
                odeploycons.GlusterEnv.MONITORING_SERVER
            ] is not None and
            os.path.exists(odeploycons.FileLocations.NRPE_CONFIG_FILE)
        ),
    )
    def _misc(self):
        with open(odeploycons.FileLocations.NRPE_CONFIG_FILE, 'r') as f:
            content = f.read().splitlines()
        newcontent = self._getNewFileContent(
            content,
            self.environment[
                odeploycons.GlusterEnv.MONITORING_SERVER
            ]
        )
        if content != newcontent:
            self._modified = True
            self.environment[
                otopicons.CoreEnv.MAIN_TRANSACTION
            ].append(
                filetransaction.FileTransaction(
                    name=odeploycons.FileLocations.NRPE_CONFIG_FILE,
                    content=newcontent,
                    modifiedList=self.environment[
                        otopicons.CoreEnv.MODIFIED_FILES
                    ],
                )
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: (
            odeploycons.GlusterEnv.MONITORING_ENABLE
        )
    )
    def _closeup(self):
        if self.services.exists('nrpe'):
            self.logger.info(_('Restarting nrpe service'))
            if self._modified:
                self.services.state('nrpe', False)
            self.services.state('nrpe', True)
            self.services.startup('nrpe', True)

# vim: expandtab tabstop=4 shiftwidth=4
