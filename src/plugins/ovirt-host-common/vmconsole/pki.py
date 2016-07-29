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


"""Serial console PKI artifacts."""


import gettext
import os
import pwd


from otopi import constants as otopicons
from otopi import filetransaction
from otopi import plugin
from otopi import util


from ovirt_host_deploy import constants as odeploycons


def _(m):
    return gettext.dgettext(message=m, domain='ovirt-host-deploy')


@util.export
class Plugin(plugin.PluginBase):
    def _genReqM2Crypto(self):
        from M2Crypto import X509, RSA, EVP

        rsa = RSA.gen_key(
            self.environment[odeploycons.VMConsoleEnv.KEY_SIZE],
            65537,
        )
        rsapem = rsa.as_pem(cipher=None)
        evp = EVP.PKey()
        evp.assign_rsa(rsa)
        rsa = None  # should not be freed here
        req = X509.Request()
        req.set_pubkey(evp)
        req.sign(evp, 'sha1')
        return rsapem, req.as_pem()

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = False
        self._cleanupFiles = []

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.VMConsoleEnv.CERTIFICATE_ENROLLMENT,
            odeploycons.Const.CERTIFICATE_ENROLLMENT_NONE
        )
        self.environment.setdefault(
            odeploycons.VMConsoleEnv.CERTIFICATE,
            None
        )
        self.environment.setdefault(
            odeploycons.VMConsoleEnv.KEY_SIZE,
            odeploycons.Defaults.DEFAULT_KEY_SIZE
        )
        self.environment.setdefault(
            odeploycons.VMConsoleEnv.CAKEY,
            None
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.VMConsoleEnv.CERTIFICATE_ENROLLMENT
        ] != odeploycons.Const.CERTIFICATE_ENROLLMENT_NONE
    )
    def _validation(self):
        if self.environment[
            odeploycons.VMConsoleEnv.CERTIFICATE_ENROLLMENT
        ] == odeploycons.Const.CERTIFICATE_ENROLLMENT_ACCEPT:
            # we cannot perform the following
            # in validation stage, as we do not have
            # the trust store location.
            if not os.path.exists(
                odeploycons.FileLocations.VMCONSOLE_KEY_PENDING_FILE
            ):
                raise RuntimeError(
                    _('PKI accept mode while no pending request')
                )

        self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        self.packager.install(('m2crypto',))

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        condition=lambda self: self._enabled,
    )
    def _misc(self):
        try:
            pwd.getpwnam('ovirt-vmconsole')
        except Exception:
            self.logger.debug(
                'ovirt-vmconsole user is missing disabling support',
                exc_info=True,
            )
            self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        priority=plugin.Stages.PRIORITY_LOW,
        condition=lambda self: self._enabled,
    )
    def _miscLate(self):
        self.dialog.note(_('Setting up Serial Console PKI'))

        enrollment = self.environment[
            odeploycons.VMConsoleEnv.CERTIFICATE_ENROLLMENT
        ]

        if enrollment == odeploycons.Const.CERTIFICATE_ENROLLMENT_ACCEPT:
            with open(
                odeploycons.FileLocations.VMCONSOLE_KEY_PENDING_FILE
            ) as f:
                key = f.read()
        else:
            key, req = self._genReqM2Crypto()

            self.dialog.displayMultiString(
                name=odeploycons.Displays.VMCONSOLE_CERTIFICATE_REQUEST,
                value=req.splitlines(),
                note=_(
                    '\n\nPlease issue serial console certificate based '
                    'on this certificate request\n\n'
                ),
            )

        if enrollment == odeploycons.Const.CERTIFICATE_ENROLLMENT_REQUEST:
            self.environment[odeploycons.CoreEnv.INSTALL_INCOMPLETE] = True
            self.environment[
                odeploycons.CoreEnv.INSTALL_INCOMPLETE_REASONS
            ].append(_('Serial console certificate enrollment required'))

            self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=odeploycons.FileLocations.VMCONSOLE_KEY_PENDING_FILE,
                    mode=0o400,
                    enforcePermissions=True,
                    content=key,
                    modifiedList=self.environment[
                        otopicons.CoreEnv.MODIFIED_FILES
                    ],
                )
            )
        else:
            self._cleanupFiles.append(
                odeploycons.FileLocations.VMCONSOLE_KEY_PENDING_FILE
            )

            cert = self.environment[
                odeploycons.VMConsoleEnv.CERTIFICATE
            ]

            if cert is None:
                cert = self.environment[
                    odeploycons.VMConsoleEnv.CERTIFICATE
                ] = self.dialog.queryValue(
                    name=odeploycons.Queries.VMCONSOLE_CERTIFICATE,
                    note=_(
                        '\n\nPlease input serial console certificate chain '
                        'that matches certificate request, top is issuer\n\n'
                    ),
                )

            self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=odeploycons.FileLocations.VMCONSOLE_CA_FILE,
                    enforcePermissions=True,
                    content='%s\n' % self.environment[
                        odeploycons.VMConsoleEnv.CAKEY
                    ],
                    modifiedList=self.environment[
                        otopicons.CoreEnv.MODIFIED_FILES
                    ],
                )
            )

            self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=odeploycons.FileLocations.VMCONSOLE_CERT_FILE,
                    enforcePermissions=True,
                    content='%s\n' % cert,
                    modifiedList=self.environment[
                        otopicons.CoreEnv.MODIFIED_FILES
                    ],
                )
            )

            self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=odeploycons.FileLocations.VMCONSOLE_KEY_FILE,
                    owner='ovirt-vmconsole',
                    group='ovirt-vmconsole',
                    mode=0o400,
                    enforcePermissions=True,
                    content=key,
                    modifiedList=self.environment[
                        otopicons.CoreEnv.MODIFIED_FILES
                    ],
                )
            )

    @plugin.event(
        stage=plugin.Stages.STAGE_CLOSEUP,
        condition=lambda self: self._enabled,
    )
    def _closeup(self):
        for f in self._cleanupFiles:
            if os.path.exists(f):
                try:
                    os.unlink(f)
                except OSError:
                    self.logger.warning(
                        _("Cannot remove file '{name}'.").format(
                            name=f,
                        )
                    )
                    self.logger.debug(exc_info=True)


# vim: expandtab tabstop=4 shiftwidth=4
