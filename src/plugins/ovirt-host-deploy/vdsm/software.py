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


import platform
from distutils.version import LooseVersion
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import util
from otopi import plugin


@util.export
class Plugin(plugin.PluginBase):
    """Hardware prerequisites plugin."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
    )
    def _validation(self):
        dist, ver = platform.linux_distribution(full_distribution_name=0)[:2]
        if dist == 'redhat':
            if LooseVersion(ver) < LooseVersion('6.2'):
                raise RuntimeError(
                    _(
                        'Distribution {distribution} version {version} '
                        'is not supported'
                    ).format(
                        distribution=dist,
                        version=ver,
                    )
                )
        elif dist == 'fedora':
            if LooseVersion(ver) < LooseVersion('17'):
                raise RuntimeError(
                    _(
                        'Distribution {distribution} version {version} '
                        'is not supported'
                    ).format(
                        distribution=dist,
                        version=ver,
                    )
                )
        else:
            raise RuntimeError(
                _('Distribution {distribution} is not supported').format(
                    distribution=dist,
                )
            )


# vim: expandtab tabstop=4 shiftwidth=4
