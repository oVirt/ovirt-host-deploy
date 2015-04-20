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

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)

dist_ovirthostdeployinterface_SCRIPTS = \
	setup \
	$(NULL)

install-data-hook:
	$(SHELL) "$(OTOPI_BUNDLE)"  \
		--gettext-domain="$(PACKAGE_NAME)" \
		--target="$(DESTDIR)$(ovirthostdeployinterfacedir)" \
		--root="$(DESTDIR)" \
		--otopi-sources="$(OTOPI_SOURCES)"
	rm -f "$(DESTDIR)$(ovirthostdeployinterfacedir)/ovirt-host-deploy"
	$(LN_SR) "$(DESTDIR)$(sbindir)/ovirt-host-deploy" "$(DESTDIR)$(ovirthostdeployinterfacedir)/ovirt-host-deploy"
	rm -f "$(DESTDIR)$(ovirthostdeployinterfacedir)/pythonlib/ovirt_host_deploy"
	$(LN_SR) "$(DESTDIR)$(ovirthostdeploylibdir)" "$(DESTDIR)$(ovirthostdeployinterfacedir)/pythonlib/ovirt_host_deploy"
	rm -f "$(DESTDIR)$(ovirthostdeployinterfacedir)/otopi-plugins/ovirt-host-deploy"
	$(LN_SR) "$(DESTDIR)$(ovirthostdeployplugindir)/ovirt-host-deploy" "$(DESTDIR)$(ovirthostdeployinterfacedir)/otopi-plugins/ovirt-host-deploy"

uninstall-hook:
	rm -f "$(DESTDIR)$(ovirthostdeployinterfacedir)/.bundled"
