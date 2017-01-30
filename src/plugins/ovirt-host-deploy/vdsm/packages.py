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


"""Install required vdsm packages."""


import gettext


from distutils.version import LooseVersion


from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    """vdsm packages plugin.

    Environment:
        VdsmEnv.VDSM_MINIMUM_VERSION -- Minimum version to validate.

    """
    def __init__(self, context):
        super(Plugin, self).__init__(context=context)

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.VdsmEnv.VDSM_MINIMUM_VERSION,
            None
        )
        self.environment.setdefault(
            odeploycons.VdsmEnv.DISABLE_NETWORKMANAGER,
            True
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        self.command.detect('vdsm-tool')

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
    )
    def _validation(self):
        result = self.packager.queryPackages(patterns=('vdsm',))
        if not result:
            raise RuntimeError(
                _(
                    'Cannot locate vdsm package, '
                    'possible cause is incorrect channels'
                )
            )
        entry = result[0]
        self.logger.debug('Found vdsm %s', entry)

        minversion = self.environment[odeploycons.VdsmEnv.VDSM_MINIMUM_VERSION]
        currentversion = '%s-%s' % (
            entry['version'],
            entry['release'],
        )
        if minversion is not None:
            # this versio object does not handle the '-' as rpm...
            if [LooseVersion(v) for v in minversion.split('-')] > \
                    [LooseVersion(v) for v in currentversion.split('-')]:
                raise RuntimeError(
                    _(
                        'VDSM package is too old, '
                        'need {minimum} found {version}'
                    ).format(
                        minimum=minversion,
                        version=currentversion,
                    )
                )

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
    )
    def _packages(self):
        if self.services.exists('vdsmd'):
            self.services.state('vdsmd', False)
        if self.services.exists('supervdsmd'):
            self.services.state('supervdsmd', False)
        self.packager.install(('qemu-kvm-tools',))
        self.packager.installUpdate(('vdsm', 'vdsm-cli'))

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
    )
    def _closeup(self):

        # libvirt-guests is a conflict
        if self.services.exists('libvirt-guests'):
            self.services.state('libvirt-guests', False)
            self.services.startup('libvirt-guests', False)

        self.services.startup('vdsmd', True)
        if not self.services.supportsDependency:
            if self.services.exists('libvirtd'):
                self.services.startup('libvirtd', True)
            if self.services.exists('messagebus'):
                self.services.startup('messagebus', True)
            if self.services.exists('cgconfig'):
                self.services.startup('cgconfig', True)

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        priority=plugin.Stages.PRIORITY_HIGH,
    )
    def _reconfigure(self):
        vdsm_tool = self.command.get(
            command='vdsm-tool',
        )
        rc, stdout, stderr = self.execute(
            (
                vdsm_tool,
                'configure',
                '--force',
            ),
            raiseOnError=False,
        )
        if rc != 0:
            self.logger.warning('Cannot configure vdsm')

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        priority=plugin.Stages.PRIORITY_LOW,
        condition=lambda self: not self.environment[
            odeploycons.CoreEnv.FORCE_REBOOT
        ],
        name=odeploycons.Stages.VDSM_STARTED,
    )
    def _start(self):
        self.logger.info(_('Stopping libvirtd'))
        if self.services.exists('libvirtd'):
            self.services.state('libvirtd', False)

        self.logger.info(_('Starting vdsm'))
        if not self.services.supportsDependency:
            if self.services.exists('cgconfig'):
                self.services.state('cgconfig', True)
            if self.services.exists('messagebus'):
                self.services.state('messagebus', True)
            if self.services.exists('libvirtd'):
                self.services.state('libvirtd', True)

        # restarts 'ovirt-imageio-daemon' service to ensure
        # that a valid certificate is loaded.
        if self.services.exists('ovirt-imageio-daemon'):
            self.services.state('ovirt-imageio-daemon', False)
            self.services.state('ovirt-imageio-daemon', True)

        #
        # remove network manager as it create timing
        # issues with the network service and vdsm
        # see rhbz#879180
        #
        if (
            self.environment[odeploycons.VdsmEnv.DISABLE_NETWORKMANAGER] and
            self.services.exists('NetworkManager')
        ):
            self.services.state('NetworkManager', False)
            self.services.startup('NetworkManager', False)

        #
        # vdsm requires network to be active
        # it cannot depend on this service as
        # it will be stopped when network is stopped
        # so we do this manually.
        #
        if self.services.exists('network'):
            # rhel network fails on second restart
            if not self.services.status('network'):
                try:
                    self.services.state('network', True)
                except RuntimeError:
                    # rhel network fails to start if one
                    # of the interfaces is failing.
                    # see rhbz#990980.
                    self.logger.debug(
                        'Cannot start network service ignoring',
                        exc_info=True,
                    )
            self.services.startup('network', True)

        self.services.state('vdsmd', True)


# vim: expandtab tabstop=4 shiftwidth=4
