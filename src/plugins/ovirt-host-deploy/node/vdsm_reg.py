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


"""vdsm-reg handling."""

import os
import configparser
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import constants as otopicons
from otopi import util
from otopi import filetransaction
from otopi import plugin


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """vdsm-reg handling.

    This to be deleted as soon as vdsm-reg dies.
    We just configure it, so it won't do anything bad.
    But we do not actually use it.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.OVIRT_NODE
        ],
    )
    def _misc(self):
        CONF = '/etc/vdsm-reg/vdsm-reg.conf'

        if self.services.exists('vdsm-reg'):
            config = configparser.ConfigParser()
            config.optionxform = str

            if os.path.exists(CONF):
                config.read([CONF])

            if not config.has_section('vars'):
                config.add_section('vars')

            config.set(
                'vars',
                'vdc_host_name',
                'None',
            )

            class buf(object):
                """io.StringIO is not working???"""
                def __init__(self):
                    self.content = ''

                def write(self, s):
                    self.content += s
            b = buf()
            config.write(b)

            # a bug in vdsm-reg prevent it from writing
            # the host name and port if there are spaces between '='
            # python always writes spaces...
            for f in ('vdc_host_name', 'vdc_host_port'):
                b.content = b.content.replace(
                    '%s = ' % f,
                    '%s=' % f,
                    1
                )

            self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=CONF,
                    content=b.content,
                    modifiedList=self.environment[
                        otopicons.CoreEnv.MODIFIED_FILES
                    ],
                )
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.OVIRT_NODE
        ],
    )
    def _closeup(self):
        if self.services.exists('vdsm-reg'):
            self.services.state('vdsm-reg', False)


# vim: expandtab tabstop=4 shiftwidth=4
