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

artifact=ovirt-host-deploy
generate=ovirt_host_deploy.constants

targetdir=$(abs_top_builddir)/target
jarname=$(artifact)-$(PACKAGE_MAVEN_VERSION).jar
targetjar=$(targetdir)/$(jarname)

MAINTAINERCLEANFILES = \
	$(srcdir)/Makefile.in \
	$(NULL)
CLEANFILES = \
	tmp.generated \
	$(targetjar) \
	$(NULL)

EXTRA_DIST = \
	.gitignore \
	$(NULL)

dist_noinst_DATA = \
	MANIFEST.MF \
	$(NULL)

if JAVA_SDK

if JAVA_SDK_COMPILE
all-local:	\
		$(targetjar) \
		$(NULL)
else
all-local:	\
		sources \
		$(NULL)
endif

clean-local:
	rm -fr src target tmp.*

if WITH_MAVEN

$(targetjar):	\
		sources \
		pom.xml \
		$(NULL)
	rm -f "$(targetjar)"
	$(MKDIR_P) "$(targetdir)"
	$(MVN) \
		-D altDeploymentRepository=install::default::file://$(targetdir)/maven \
		deploy
	cp "$(targetdir)/maven/org/ovirt/$(PACKAGE_NAME)/$(artifact)/$(PACKAGE_MAVEN_VERSION)$(MAVEN_VERSION_SNAPSHOT)"/$$(echo $(jarname) | sed 's/\.jar/*.jar/') "$(targetdir)"

else

$(targetjar):	\
		sources \
		$(NULL)
	rm -f "$(targetjar)"
	$(MKDIR_P) "$(targetdir)"
	$(MKDIR_P) target
	$(JAVAC) -d target `find src/main/java -name '*.java'`
	$(JAR) -cmf $(srcdir)/MANIFEST.MF "$(targetjar)" -C target .

endif

sources: \
		tmp.generated \
		$(NULL)

# TODO: kill __main__ when python-2.6 gone
tmp.generated:
	rm -f tmp.generated
	PYTHONPATH="$(OTOPI_SOURCES)/src:$(srcdir)/..:${PYTHONPATH}" $(PYTHON) \
		-m otopi.codegen.__main__ \
		src/main/java \
		org.ovirt \
		$(generate)
	touch tmp.generated

endif
