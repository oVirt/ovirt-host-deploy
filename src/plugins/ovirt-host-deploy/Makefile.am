#
# ovirt-host-deploy -- ovirt host deployer
# Copyright (C) 2012-2017 Red Hat, Inc.
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

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)

SUBDIRS = \
	cockpit \
	core \
	gluster \
	host \
	kdump \
	kernel \
	node \
	tune \
	vdsm \
	vdsmhooks \
	vmconsole \
	$(NULL)

install-data-local:
	$(MKDIR_P) "$(DESTDIR)$(otopiplugindir)"
	rm -f "$(DESTDIR)$(otopiplugindir)/ovirt-host-deploy"
	ln -s "$(ovirthostdeployplugindir)/ovirt-host-deploy" "$(DESTDIR)$(otopiplugindir)/ovirt-host-deploy"
