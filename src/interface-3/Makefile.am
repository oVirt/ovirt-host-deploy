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

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in

install-data-hook:
	$(SHELL) "$(OTOPI_BUNDLE)"  \
		--gettext-domain="$(PACKAGE_NAME)" \
		--target="$(DESTDIR)$(ovirthostdeployinterfacedir)" \
		--root="$(DESTDIR)" \
		--otopi-sources="$(OTOPI_SOURCES)"
	rm -f "$(DESTDIR)$(ovirthostdeployinterfacedir)/$(PACKAGE_NAME)"
	$(LN_SR) "$(DESTDIR)$(sbindir)/$(PACKAGE_NAME)" "$(DESTDIR)$(ovirthostdeployinterfacedir)/$(PACKAGE_NAME)"
	rm -f "$(DESTDIR)$(ovirthostdeployinterfacedir)/pythonlib/ovirt_host_deploy"
	$(LN_SR) "$(DESTDIR)$(ovirthostdeploylibdir)" "$(DESTDIR)$(ovirthostdeployinterfacedir)/pythonlib/ovirt_host_deploy"
	rm -f "$(DESTDIR)$(ovirthostdeployinterfacedir)/otopi-plugins/$(PACKAGE_NAME)"
	$(LN_SR) "$(DESTDIR)$(ovirthostdeployplugindir)/$(PACKAGE_NAME)" "$(DESTDIR)$(ovirthostdeployinterfacedir)/otopi-plugins/$(PACKAGE_NAME)"
	rm -f "$(DESTDIR)$(ovirthostdeployinterfacedir)/setup"
	ln -s $(PACKAGE_NAME) "$(DESTDIR)$(ovirthostdeployinterfacedir)/setup"

uninstall-hook:
	rm -f "$(DESTDIR)$(ovirthostdeployinterfacedir)/.bundled"
