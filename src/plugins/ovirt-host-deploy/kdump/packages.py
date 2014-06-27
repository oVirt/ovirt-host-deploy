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


"""kdump packages plugin."""


import gettext
import platform
import re


from otopi import util
from otopi import plugin
from otopi import constants as otopicons
from otopi import filetransaction

from ovirt_host_deploy import constants as odeploycons


_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """Required packages installation.

    Environment:
        KdumpEnv.ENABLE              -- perform kdump detection configuration
        KdumpEnv.SUPPORTED           -- kexec-tools package supports
                                        fence_kdump configuration
        KdumpEnv.DESTINATION_ADDRESS -- server to send fence_kdump messages to
        KdumpEnv.DESTINATION_PORT    -- port to send fence_kdump messages to
        KdumpEnv.MESSAGE_INTERVAL    -- interval between fence_kdump messages

    """

    _KEXEC_TOOLS_PKG = 'kexec-tools'

    # pattern to match lines with fence_kdump configuration
    _FK_OPTS_REGEX = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            fence_kdump_(nodes|args)
            \s
            .*
            $
        """
    )

    # pattern to match lines with ovirt-host-deploy configuration backup
    _FK_BACKUP_REGEX = re.compile(
        flags=re.VERBOSE,
        pattern=r"""
            ^
            \#ovirt-host-deploy:backup-begin
            .*
            $
        """
    )

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = True

    def _get_min_kexec_tools_version(self):
        (name, version, desc) = platform.linux_distribution(
            full_distribution_name=0
        )

        min_version = None
        if name in ('redhat', 'centos'):
            major = version.split('.', 1)[0]
            if major == '6':
                min_version = None, '2.0.0', '273.1'
            elif major == '7':
                min_version = None, '2.0.4', '32.1'

        elif name == 'fedora':
            min_version = None, '2.0.4', '27'

        return min_version

    def _crashkernel_param_present(self):
        crashkernel = False
        with open('/proc/cmdline') as f:
            for line in f.read().splitlines():
                if 'crashkernel=' in line:
                    crashkernel = True
                    break
        return crashkernel

    def _update_kdump_conf(
            self,
            content,
            engine_node,
            port,
            interval,
    ):
        new_content = []
        backup = []
        backup_exists = False

        for line in content:
            if self._FK_OPTS_REGEX.match(line) is not None:
                # line with fence_kdump config
                backup.append(line)
            else:
                if self._FK_BACKUP_REGEX.match(line) is not None:
                    # line with fence_kdump config backup
                    backup_exists = True

                new_content.append(line)

        if not backup_exists and backup:
            new_content.append('#ovirt-host-deploy:backup-begin')
            new_content.extend(['#' + l for l in backup])
            new_content.append('#ovirt-host-deploy:backup-end')

        new_content.extend(
            (
                'fence_kdump_nodes %s' % (
                    engine_node,
                ),
                'fence_kdump_args -p %s -i %s' % (
                    port,
                    interval,
                ),
            )
        )
        return new_content

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(odeploycons.KdumpEnv.ENABLE, False)
        self.environment.setdefault(odeploycons.KdumpEnv.SUPPORTED, False)

    @plugin.event(
        stage=plugin.Stages.STAGE_CUSTOMIZATION,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _customization(self):
        if self._crashkernel_param_present():
            # crashkernel param set, check for required kexec-tools version
            min_version = self._get_min_kexec_tools_version()
            if min_version is not None:
                from rpmUtils.miscutils import compareEVR
                result = self.packager.queryPackages(
                    patterns=(self._KEXEC_TOOLS_PKG,),
                )
                self.logger.debug("minver: %s, result=%s", min_version, result)
                for package in result:
                    cur_version = (
                        None,
                        package['version'],
                        package['release'],
                    )
                    if compareEVR(cur_version, min_version) >= 0:
                        self.environment[odeploycons.KdumpEnv.SUPPORTED] = True
                        break

        self.logger.info(
            _('Kdump {result}').format(
                result=(
                    'supported'
                    if self.environment[odeploycons.KdumpEnv.SUPPORTED]
                    else 'unsupported'
                ),
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self.environment[odeploycons.KdumpEnv.ENABLE],
    )
    def _packages(self):
        self.packager.installUpdate(
            packages=(self._KEXEC_TOOLS_PKG,),
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self.environment[odeploycons.KdumpEnv.ENABLE],
    )
    def _misc(self):
        with open(odeploycons.FileLocations.KDUMP_CONFIG_FILE, 'r') as f:
            content = f.read().splitlines()

        new_content = self._update_kdump_conf(
            content=content,
            engine_node=self.environment[
                odeploycons.KdumpEnv.DESTINATION_ADDRESS
            ],
            port=self.environment[
                odeploycons.KdumpEnv.DESTINATION_PORT
            ],
            interval=self.environment[
                odeploycons.KdumpEnv.MESSAGE_INTERVAL
            ],
        )

        self.environment[
            otopicons.CoreEnv.MAIN_TRANSACTION
        ].append(
            filetransaction.FileTransaction(
                name=odeploycons.FileLocations.KDUMP_CONFIG_FILE,
                content=new_content,
                modifiedList=self.environment[
                    otopicons.CoreEnv.MODIFIED_FILES
                ],
            )
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self.environment[odeploycons.KdumpEnv.ENABLE],
    )
    def _closeup(self):
        self.logger.info(_('Restarting kdump'))
        self.services.startup('kdump', True)
        for state in (False, True):
            self.services.state('kdump', state)


# vim: expandtab tabstop=4 shiftwidth=4