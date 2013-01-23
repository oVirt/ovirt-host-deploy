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


"""vdsm hooks installation."""


import os
import platform
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import constants as otopicons
from otopi import util
from otopi import plugin
from otopi import filetransaction


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """vdsm hooks installation."""
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
    )
    def _hooks(self):
        pluginhooksdir = os.path.join(
            os.path.dirname(__file__),
            odeploycons.FileLocations.HOOKS_PLUGIN_HOOKS_DIR,
        )
        if os.path.exists(pluginhooksdir):
            for (pathname, __, files) in os.walk(pluginhooksdir):
                rel = os.path.relpath(
                    pathname,
                    pluginhooksdir
                )
                for name in files:
                    if name.startswith('.'):
                        continue

                    with open(
                        os.path.join(
                            pathname,
                            name
                        ),
                        'r'
                    ) as f:
                        content = f.read()

                    self.environment[
                        otopicons.CoreEnv.MAIN_TRANSACTION
                    ].append(
                        filetransaction.FileTransaction(
                            name=os.path.join(
                                odeploycons.FileLocations.HOOKS_DIR,
                                rel,
                                name,
                            ),
                            owner='root',
                            enforcePermissions=True,
                            content=content,
                            modifiedList=self.environment[
                                otopicons.CoreEnv.MODIFIED_FILES
                            ],
                        )
                    )

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
    )
    def _packages(self):
        pluginpackagesdir = os.path.join(
            os.path.dirname(__file__),
            odeploycons.FileLocations.HOOKS_PLUGIN_PACKAGES_DIR,
        )
        if os.path.exists(pluginpackagesdir):
            for name in sorted(os.listdir(pluginpackagesdir)):
                if name.startswith('.'):
                    continue
                if name.endswith(platform.linux_distribution()):
                    with open(name, 'r') as f:
                        for package in f:
                            self.packager.installUpdate(package)


# vim: expandtab tabstop=4 shiftwidth=4
