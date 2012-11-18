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


"""vdsm plugin."""


from otopi import util


from . import vdsmid
from . import pki
from . import hardware
from . import software
from . import packages
from . import tuned
from . import config
from . import bridge


@util.export
def createPlugins(context):
    vdsmid.Plugin(context=context)
    pki.Plugin(context=context)
    hardware.Plugin(context=context)
    software.Plugin(context=context)
    packages.Plugin(context=context)
    tuned.Plugin(context=context)
    config.Plugin(context=context)
    bridge.Plugin(context=context)
