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


"""ovirt-node peristance."""


import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import constants as otopicons
from otopi import util
from otopi import plugin


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """ovirt-node persistance."""

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        priority=plugin.Stages.PRIORITY_LAST,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.OVIRT_NODE
        ],
    )
    def _closeup(self):
        _persist = None
        try:
            # First: Try importing the new code,
            # this should work most of the time
            from ovirt.node.utils.fs import Config
            _persist = lambda f: Config().persist(f)
        except ImportError:
            try:
                # If it failed, then try importing the legacy code
                from ovirtnode import ovirtfunctions
                _persist = lambda f: ovirtfunctions.ovirt_store_config(f)
            except ImportError:
                raise RuntimeError(_('Cannot resolve persist module.'))

        for f in (
            [odeploycons.FileLocations.VDSM_ID_FILE] +
            self.environment[otopicons.CoreEnv.MODIFIED_FILES]
        ):
            self.logger.debug('persisting: %s' % f)
            _persist(f)


# vim: expandtab tabstop=4 shiftwidth=4
