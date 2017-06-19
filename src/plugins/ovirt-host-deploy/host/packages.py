#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2017 Red Hat, Inc.
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


"""Install required oVirt Host package."""


import gettext


from distutils.version import LooseVersion


from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """oVirt Host package plugin.

    Environment:
        OvirtHost.OVIRT_HOST_MINIMUM_VERSION -- Minimum version to validate.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.OvirtHost.OVIRT_HOST_MINIMUM_VERSION,
            None
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
    )
    def _validation(self):
        result = self.packager.queryPackages(patterns=('ovirt-host',))
        if not result:
            raise RuntimeError(
                _(
                    'Cannot locate ovirt-host package, '
                    'possible cause is incorrect channels'
                )
            )
        entry = result[0]
        self.logger.debug('Found ovirt-host %s', entry)

        minversion = self.environment[
            odeploycons.OvirtHost.OVIRT_HOST_MINIMUM_VERSION
        ]
        currentversion = '%s-%s' % (
            entry['version'],
            entry['release'],
        )
        if minversion is not None:
            # this version object does not handle the '-' as rpm...
            if [LooseVersion(v) for v in minversion.split('-')] > \
                    [LooseVersion(v) for v in currentversion.split('-')]:
                raise RuntimeError(
                    _(
                        'oVirt Host package is too old, '
                        'need {minimum} found {version}'
                    ).format(
                        minimum=minversion,
                        version=currentversion,
                    )
                )

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        name=odeploycons.Stages.OVIRT_HOST_INSTALLED,
    )
    def _packages(self):
        self.packager.installUpdate(('ovirt-host',))


# vim: expandtab tabstop=4 shiftwidth=4
