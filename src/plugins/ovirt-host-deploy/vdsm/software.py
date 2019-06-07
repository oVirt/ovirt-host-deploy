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


"""vdsm software prerequisites plugin."""


import gettext
import platform


from distutils.version import LooseVersion


from otopi import plugin
from otopi import util


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """Software prerequisites plugin."""

    _SUPPORTED = [
        {
            'distro': ('redhat', 'centos'),
            'version': '7.5',
        },
        {
            'distro': ('fedora', ),
            'version': '24',
        },
    ]

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
    )
    def _validation(self):
        dist, ver = platform.linux_distribution(full_distribution_name=0)[:2]

        supported = False
        for entry in self._SUPPORTED:
            if (
                dist in entry['distro'] and
                LooseVersion(ver) >= LooseVersion(entry['version'])
            ):
                supported = True
                break

        if not supported:
            raise RuntimeError(
                _(
                    'Distribution {distribution} version {version} '
                    'is not supported'
                ).format(
                    distribution=dist,
                    version=ver,
                )
            )


# vim: expandtab tabstop=4 shiftwidth=4
