#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2012 Red Hat, Inc.
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


"""Handle vdsm PKI artifacts."""


import os
import configparser
import gettext
_ = lambda m: gettext.dgettext(message=m, domain='ovirt-host-deploy')


from otopi import constants as otopicons
from otopi import util
from otopi import filetransaction
from otopi import plugin


from ovirt_host_deploy import constants as odeploycons


@util.export
class Plugin(plugin.PluginBase):
    """PKI plugin.

    Environment:
        VdsmEnv.CERTIFICATE_ENROLLMENT -- enrollment type.
        VdsmEnv.CERTIFICATE_CHAIN -- chain to accept.
        VdsmEnv.KEY_SIZE -- RSA key size.

    Queries:
        Queries.CERTIFICATE_CHAIN -- query certificate chain.

    Displays
        Displays.CERTIFICATE_REQUEST -- present certificate request.

    """
    def _isM2Crypto(self):
        try:
            import M2Crypto
            type(M2Crypto)
            return True
        except ImportError:
            return False

    def _genReqM2Crypto(self):
        from M2Crypto import X509, RSA, EVP

        rsa = RSA.gen_key(
            self.environment[odeploycons.VdsmEnv.KEY_SIZE],
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

    def _getChainM2Crypto(self, chain):
        from M2Crypto import X509, BIO

        cacert = None
        vdsmchain = ''
        bio = None
        try:
            bio = BIO.MemoryBuffer('\n'.join(chain).encode('utf-8'))

            try:
                cacert = X509.load_cert_bio(
                    bio=bio,
                    format=X509.FORMAT_PEM
                ).as_pem()
            except X509.X509Error:
                self.logger.debug(
                    'read vdsm certificate chain',
                    exc_info=True
                )
                raise RuntimeError(_('CA Certificate was not provided'))

            try:
                while True:
                    vdsmchain += X509.load_cert_bio(
                        bio=bio,
                        format=X509.FORMAT_PEM
                    ).as_pem()
            except X509.X509Error:
                if not vdsmchain:
                    self.logger.debug(
                        'read vdsm certificate chain',
                        exc_info=True
                    )

                    raise RuntimeError(
                        _('VDM Certificate was not provided')
                    )

            return (cacert, vdsmchain)
        finally:
            if bio is not None:
                bio.close()

    def _genReqOpenSSL(self):
        """issue via openssl use file"""
        import tempfile
        fd, tmpfile = tempfile.mkstemp(
            suffix=".tmp",
        )
        os.close(fd)
        try:
            rc, stdout, stderr = self.execute(
                (
                    self.command.get('openssl'),
                    'req',
                    '-new',
                    '-newkey', 'rsa:%s' % (
                        self.environment[odeploycons.VdsmEnv.KEY_SIZE]
                    ),
                    '-nodes',
                    '-subj', '/',
                    '-keyout', tmpfile
                )
            )
            with open(tmpfile, 'r') as f:
                rsapem = f.read()
        finally:
            os.unlink(tmpfile)

        return rsapem, '\n'.join(stdout)

    def _getChainOpenSSL(self, chain):
        """perform primitive loop"""
        cacert = ''
        vdsmchain = ''
        inca = True
        for line in chain:
            if inca:
                cacert += line + '\n'
            else:
                vdsmchain += line + '\n'
            if line.find('-END CERTIFICATE-') != -1:
                inca = False

        return (cacert, vdsmchain)

    def __init__(self, context):
        super(Plugin, self).__init__(context=context)
        self._enabled = False

    @plugin.event(
        stage=plugin.Stages.STAGE_INIT,
    )
    def _init(self):
        self.environment.setdefault(
            odeploycons.VdsmEnv.CERTIFICATE_ENROLLMENT,
            odeploycons.Const.CERTIFICATE_ENROLLMENT_INLINE
        )
        self.environment.setdefault(
            odeploycons.VdsmEnv.CERTIFICATE_CHAIN,
            None
        )
        self.environment.setdefault(
            odeploycons.VdsmEnv.KEY_SIZE,
            odeploycons.Defaults.DEFAULT_KEY_SIZE
        )

    @plugin.event(
        stage=plugin.Stages.STAGE_SETUP,
    )
    def _setup(self):
        # TODO:
        # remove when node comes with m2crypto
        self.command.detect('openssl')

    @plugin.event(
        stage=plugin.Stages.STAGE_VALIDATION,
        condition=lambda self: self.environment[
            odeploycons.VdsmEnv.CERTIFICATE_ENROLLMENT
        ] != odeploycons.Const.CERTIFICATE_ENROLLMENT_NONE,
    )
    def _validation(self):
        if (
            self.environment[
                odeploycons.VdsmEnv.CERTIFICATE_ENROLLMENT
            ] == odeploycons.Const.CERTIFICATE_ENROLLMENT_ACCEPT and
            not os.path.exists(odeploycons.FileLocations.VDSM_KEY_PENDING_FILE)
        ):
            raise RuntimeError(_('PKI accept mode while no pending request'))
        self._enabled = True

    @plugin.event(
        stage=plugin.Stages.STAGE_PACKAGES,
        condition=lambda self: self._enabled,
    )
    def _packages(self):
        self.packager.install(('m2crypto',))

    @plugin.event(
        stage=plugin.Stages.STAGE_MISC,
        priority=plugin.Stages.PRIORITY_LOW,
        condition=lambda self: self._enabled,
    )
    def _misc(self):
        self.dialog.note(_('Setting up PKI'))

        vdsmTrustStore = odeploycons.FileLocations.VDSM_TRUST_STORE
        if os.path.exists(odeploycons.FileLocations.VDSM_CONFIG_FILE):
            config = configparser.ConfigParser()
            config.read([odeploycons.FileLocations.VDSM_CONFIG_FILE])
            try:
                vdsmTrustStore = config.get('vars', 'trust_store_path')
            except:
                pass

        useM2Crypto = self._isM2Crypto()
        enrollment = self.environment[
            odeploycons.VdsmEnv.CERTIFICATE_ENROLLMENT
        ]

        if enrollment == odeploycons.Const.CERTIFICATE_ENROLLMENT_ACCEPT:
            with open(
                odeploycons.FileLocations.VDSM_KEY_PENDING_FILE,
                'r'
            ) as f:
                vdsmkey = f.read()
        else:
            if useM2Crypto:
                vdsmkey, req = self._genReqM2Crypto()
            else:
                vdsmkey, req = self._genReqOpenSSL()

            self.dialog.displayMultiString(
                name=odeploycons.Displays.CERTIFICATE_REQUEST,
                value=req.splitlines(),
                note=_(
                    '\n\nPlease issue VDSM certificate based '
                    'on this certificate request\n\n'
                ),
            )

        if enrollment == odeploycons.Const.CERTIFICATE_ENROLLMENT_REQUEST:
            self.environment[odeploycons.CoreEnv.INSTALL_INCOMPLETE] = True
            self.environment[
                odeploycons.CoreEnv.INSTALL_INCOMPLETE_REASONS
            ].append(_('Certificate enrollment required'))

            self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                filetransaction.FileTransaction(
                    name=os.path.join(
                        vdsmTrustStore,
                        odeploycons.FileLocations.VDSM_KEY_PENDING_FILE,
                    ),
                    owner='root',
                    downer='vdsm',
                    dgroup='kvm',
                    mode=0o400,
                    dmode=0o700,
                    enforcePermissions=True,
                    content=vdsmkey,
                    modifiedList=self.environment[
                        otopicons.CoreEnv.MODIFIED_FILES
                    ],
                )
            )
        else:
            chain = self.environment[
                odeploycons.VdsmEnv.CERTIFICATE_CHAIN
            ]

            if chain is None:
                chain = self.dialog.queryMultiString(
                    name=odeploycons.Queries.CERTIFICATE_CHAIN,
                    note=_(
                        '\n\nPlease input VDSM certificate chain that '
                        'matches certificate request, top is issuer\n\n'
                    ),
                )

            if useM2Crypto:
                cacert, vdsmchain = self._getChainM2Crypto(chain)
            else:
                cacert, vdsmchain = self._getChainOpenSSL(chain)

            for f in (
                os.path.join(
                    vdsmTrustStore,
                    odeploycons.FileLocations.VDSM_CA_FILE,
                ),
                os.path.join(
                    vdsmTrustStore,
                    odeploycons.FileLocations.VDSM_SPICE_CA_FILE,
                ),
                os.path.join(
                    odeploycons.FileLocations.LIBVIRT_DEFAULT_TRUST_STORE,
                    odeploycons.FileLocations.LIBVIRT_DEFAULT_CLIENT_CA_FILE,
                ),
            ):
                self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                    filetransaction.FileTransaction(
                        name=f,
                        owner='root',
                        enforcePermissions=True,
                        content=cacert,
                        modifiedList=self.environment[
                            otopicons.CoreEnv.MODIFIED_FILES
                        ],
                    )
                )

            for f in (
                os.path.join(
                    vdsmTrustStore,
                    odeploycons.FileLocations.VDSM_CERT_FILE,
                ),
                os.path.join(
                    vdsmTrustStore,
                    odeploycons.FileLocations.VDSM_SPICE_CERT_FILE,
                ),
                os.path.join(
                    odeploycons.FileLocations.LIBVIRT_DEFAULT_TRUST_STORE,
                    odeploycons.FileLocations.LIBVIRT_DEFAULT_CLIENT_CERT_FILE,
                ),
            ):
                self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                    filetransaction.FileTransaction(
                        name=f,
                        owner='root',
                        enforcePermissions=True,
                        content=vdsmchain,
                        modifiedList=self.environment[
                            otopicons.CoreEnv.MODIFIED_FILES
                        ],
                    )
                )

            for f in (
                os.path.join(
                    vdsmTrustStore,
                    odeploycons.FileLocations.VDSM_KEY_FILE,
                ),
                os.path.join(
                    vdsmTrustStore,
                    odeploycons.FileLocations.VDSM_SPICE_KEY_FILE,
                ),
                os.path.join(
                    odeploycons.FileLocations.LIBVIRT_DEFAULT_TRUST_STORE,
                    odeploycons.FileLocations.LIBVIRT_DEFAULT_CLIENT_KEY_FILE,
                ),
            ):
                self.environment[otopicons.CoreEnv.MAIN_TRANSACTION].append(
                    filetransaction.FileTransaction(
                        name=f,
                        owner='vdsm',
                        group='kvm',
                        downer='vdsm',
                        dgroup='kvm',
                        mode=0o440,
                        dmode=0o750,
                        enforcePermissions=True,
                        content=vdsmkey,
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
        if self.environment[
            odeploycons.VdsmEnv.CERTIFICATE_ENROLLMENT
        ] != odeploycons.Const.CERTIFICATE_ENROLLMENT_REQUEST:
            if os.path.exists(odeploycons.FileLocations.VDSM_KEY_PENDING_FILE):
                os.unlink(odeploycons.FileLocations.VDSM_KEY_PENDING_FILE)
