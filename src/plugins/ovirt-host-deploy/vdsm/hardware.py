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


"""vdsm hardware prerequisites plugin."""


import gettext


from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons
from ovirt_host_deploy import hardware


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """Detect hardware virtualization properties.

    Environment:
        VdsmEnv.CHECK_VIRT_HARDWARE -- enable hardware detection.

    """

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.environment.setdefault(
            odeploycons.VdsmEnv.CHECK_VIRT_HARDWARE,
            True
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.CHECK_VIRT_HARDWARE
        ],
    )
    def _validate_virtualization(self):
        virtualization = hardware.Virtualization()
        result = virtualization.detect()
        if result == virtualization.DETECT_RESULT_UNSUPPORTED:
            raise RuntimeError(
                _('Hardware does not support virtualization')
            )
        elif result == virtualization.DETECT_RESULT_SUPPORTED:
            self.logger.info(_('Hardware supports virtualization'))
        else:
            self.logger.warning(
                _('Cannot detect if hardware supports virtualization')
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.CHECK_VIRT_HARDWARE
        ],
    )
    def _validate_optional(self):
        cpu = hardware.CPU()
        if cpu.getVendor() in (cpu.CPU_INTEL, cpu.CPU_AMD):
            with open('/proc/cpuinfo', 'r') as f:
                if 'constant_tsc' not in f.read():
                    self.logger.warning(
                        _(
                            'Machine does not support constant '
                            'timestamp counter, this may effect performance'
                        )
                    )


# vim: expandtab tabstop=4 shiftwidth=4
