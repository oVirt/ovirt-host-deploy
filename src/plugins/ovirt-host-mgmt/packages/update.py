#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2012-2015 Red Hat, Inc.
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


"""Misc plugin."""


import gettext
import platform


from otopi import plugin
from otopi import util


from ovirt_host_mgmt import constants as omgmt


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """Packages plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            omgmt.PackagesEnv.UPDATE_MODE,
            omgmt.Const.PACKAGES_UPDATE_MODE_DISABLED
        )
        self.environment.setdefault(
            omgmt.PackagesEnv.PACKAGES,
            []
        )
        self.environment[omgmt.PackagesEnv.PACKAGES_INFO] = []

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: (
            self.environment[
                omgmt.PackagesEnv.UPDATE_MODE
            ] == omgmt.Const.PACKAGES_UPDATE_MODE_CHECK_UPDATE
        ),
    )
    def _packagesCheck(self):
        info = []
        if platform.linux_distribution(
            full_distribution_name=0
        )[0] not in ('redhat', 'fedora', 'centos', 'ibm_powerkvm'):
            for entry in self.packager.queryPackages(
                patterns=self.environment[omgmt.PackagesEnv.PACKAGES],
            ):
                if entry['operation'] in ('available', 'updates'):
                    info.append(
                        '%s-%s-%s' % (
                            entry['name'],
                            entry['version'],
                            entry['release'],
                        )
                    )
        else:
            from otopi import miniyum

            class MyMiniYumSink(miniyum.MiniYumSinkBase):
                def __init__(self, log):
                    super(MyMiniYumSink, self).__init__()
                    self._log = log

                def verbose(self, msg):
                    super(MyMiniYumSink, self).verbose(msg)
                    self._log.debug('Yum: %s', msg)

                def info(self, msg):
                    super(MyMiniYumSink, self).info(msg)
                    self._log.info('Yum: %s', msg)

                def error(self, msg):
                    super(MyMiniYumSink, self).error(msg)
                    self._log.error('Yum: %s', msg)

            myum = miniyum.MiniYum(
                sink=MyMiniYumSink(self.logger),
                disabledPlugins=('versionlock',),
            )
            with myum.transaction():
                myum.install(
                    packages=self.environment[omgmt.PackagesEnv.PACKAGES],
                )
                myum.update(
                    packages=self.environment[omgmt.PackagesEnv.PACKAGES],
                )
                if myum.buildTransaction():
                    for entry in myum.queryTransaction():
                        if entry[
                            'operation'
                        ] in (
                            'update',
                            'install',
                            'obsoleting',
                        ):
                            info.append(
                                '%s-%s-%s' % (
                                    entry['name'],
                                    entry['version'],
                                    entry['release'],
                                )
                            )
        self.environment[omgmt.PackagesEnv.PACKAGES_INFO] = info

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: (
            self.environment[
                omgmt.PackagesEnv.UPDATE_MODE
            ] == omgmt.Const.PACKAGES_UPDATE_MODE_UPDATE
        ),
    )
    def _packagesUpdate(self):
        self.packager.installUpdate(
            packages=self.environment[omgmt.PackagesEnv.PACKAGES],
        )


# vim: expandtab tabstop=4 shiftwidth=4
