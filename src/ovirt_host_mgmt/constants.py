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


"""Constants."""


from otopi import util


@util.export
class FileLocations(object):
    OVIRT_HOST_MGMT_CONFIG_FILE = '/etc/ovirt-host-mgmt.conf'

    OVIRT_HOST_MGMT_LOG_PREFIX = 'ovirt-host-mgmt'


@util.export
@util.codegen
class Const(object):
    PACKAGES_UPDATE_MODE_DISABLED = "disabled"
    PACKAGES_UPDATE_MODE_CHECK_UPDATE = "checkUpdate"
    PACKAGES_UPDATE_MODE_UPDATE = "update"


@util.export
@util.codegen
class CoreEnv(object):
    OFFLINE_PACKAGER = 'OMGMT_CORE/offlinePackager'


@util.export
@util.codegen
class PackagesEnv(object):
    UPDATE_MODE = 'OMGMT_PACKAGES/packagesUpdateMode'
    PACKAGES = 'OMGMT_PACKAGES/packages'
    PACKAGES_INFO = 'OMGMT_PACKAGES/packagesInfo'


# vim: expandtab tabstop=4 shiftwidth=4
