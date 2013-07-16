dnl
dnl ovirt-host-deploy -- ovirt host deployer
dnl Copyright (C) 2012-2013 Red Hat, Inc.
dnl
dnl This library is free software; you can redistribute it and/or
dnl modify it under the terms of the GNU Lesser General Public
dnl License as published by the Free Software Foundation; either
dnl version 2.1 of the License, or (at your option) any later version.
dnl
dnl This library is distributed in the hope that it will be useful,
dnl but WITHOUT ANY WARRANTY; without even the implied warranty of
dnl MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the GNU
dnl Lesser General Public License for more details.
dnl
dnl You should have received a copy of the GNU Lesser General Public
dnl License along with this library; if not, write to the Free Software
dnl Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA
dnl
AC_PREREQ(2.60)

define([VERSION_MAJOR], [1])
define([VERSION_MINOR], [1])
define([VERSION_FIX], [0])
define([VERSION_NUMBER], VERSION_MAJOR[.]VERSION_MINOR[.]VERSION_FIX)
define([VERSION_SUFFIX], [_beta])

AC_INIT([ovirt-host-deploy], VERSION_NUMBER[]VERSION_SUFFIX)
PACKAGE_RPM_VERSION="VERSION_NUMBER"
PACKAGE_RPM_RELEASE="0.1.$(echo VERSION_SUFFIX | sed 's/^_//')"
PACKAGE_MAVEN_VERSION="VERSION_MAJOR.VERSION_MINOR.0$(echo VERSION_SUFFIX | sed 's/^_/-/')"
INTERFACE_VERSION=3
AC_SUBST([PACKAGE_RPM_VERSION])
AC_SUBST([PACKAGE_RPM_RELEASE])
AC_SUBST([PACKAGE_MAVEN_VERSION])
AC_SUBST([INTERFACE_VERSION])

AC_CONFIG_AUX_DIR([.])
AC_CONFIG_SRCDIR([src/ovirt_host_deploy/__init__.py])
AC_CONFIG_MACRO_DIR([m4])
AC_USE_SYSTEM_EXTENSIONS
AM_INIT_AUTOMAKE
AM_GNU_GETTEXT_VERSION([0.17])
AM_GNU_GETTEXT([external])

AC_ARG_ENABLE(
	[python-syntax-check],
	[AS_HELP_STRING([--disable-python-syntax-check], [disable python syntax check @<:@default=enabled@:>@])],
	,
	[enable_python_syntax_check="yes"]
)

AC_ARG_ENABLE(
	[java-sdk],
	[AS_HELP_STRING([--enable-java-sdk], [enable java-sdk @<:@default=disabled@:>@])],
	,
	[enable_java_sdk="no"]
)

AC_ARG_ENABLE(
	[java-sdk-compile],
	[AS_HELP_STRING([--disable-java-sdk-compile], [disable java-sdk compile @<:@default=enabled@:>@])],
	,
	[enable_java_sdk_compile="yes"]
)

AC_ARG_WITH(
	[maven],
	[AS_HELP_STRING([--with-maven], [use maven to build java-sdk @<:@default=no@:>@])],
	,
	[with_maven="no"]
)

AC_ARG_WITH(
	[otopi-sources],
	[AS_HELP_STRING([--with-otopi-sources], [use otopi source instead of installed @<:@default=no@:>@])],
	,
	[with_otopi_sources="no"]
)

AC_ARG_WITH(
	[maven-version-snapshot],
	[AS_HELP_STRING([--with-maven-version-snapshot], [maven version snapshot @<:@default=no@:>@])],
	,
	[with_maven_version_snapshot="no"]
)

AC_PROG_INSTALL
AC_PROG_SED
AC_PROG_MAKE_SET
AC_PROG_MKDIR_P
AC_PROG_LN_S
AX_LN_SR

AC_ARG_VAR([PYFLAKES], [path to pyflakes utility])
AC_CHECK_PROGS([PYFLAKES], [pyflakes])
AC_ARG_VAR([PEP8], [path to pep8 utility])
AC_CHECK_PROGS([PEP8], [pep8])
AC_ARG_VAR([RPMBUILD], [path to rpmbuild utility])
AC_CHECK_PROGS([RPMBUILD], [rpmbuild])
AC_ARG_VAR([MVN], [path to mvn utility])
AC_CHECK_PROGS([MVN], [mvn])
AC_ARG_VAR([JAVAC], [path to java compiler])
AC_CHECK_PROGS([JAVAC], [javac])
AC_ARG_VAR([jar], [path to jar utility])
AC_CHECK_PROGS([JAR], [jar])
AC_ARG_VAR([OTOPI_BUNDLE], [path to otopi-bundle utility])
AC_PATH_PROGS([OTOPI_BUNDLE], [otopi-bundle],, [/usr/share/otopi])

if test "${enable_java_sdk}" = "yes" -a "${enable_java_sdk_compile}" = "yes"; then
	if test "${with_maven}" = "yes"; then
		test -z "${MVN}" && \
			AC_MSG_ERROR([maven is required but not found])
	else
		test -z "${JAVAC}" && \
			AC_MSG_ERROR([javac is required but not found])
		test -z "${JAR}" && \
			AC_MSG_ERROR([jar is required but not found])
	fi
fi

if test "${with_otopi_sources}" != "no"; then
	OTOPI_BUNDLE="${with_otopi_sources}/build/otopi-bundle"
	OTOPI_SOURCES="${with_otopi_sources}"
fi

if test "${with_maven_version_snapshot}" = "no"; then
	MAVEN_VERSION_SNAPSHOT=""
else
	MAVEN_VERSION_SNAPSHOT="-SNAPSHOT"
fi
AC_SUBST([MAVEN_VERSION_SNAPSHOT])

AM_PATH_PYTHON([2.6],, [AC_MSG_ERROR([Cannot find python])])
if test "${with_otopi_sources}" = "no"; then
	AX_PYTHON_MODULE([otopi], [fatal])
fi

test -z "${OTOPI_BUNDLE}" && AC_MSG_ERROR([otopi-bundle required but missing])

otopiplugindir="\$(datadir)/otopi/plugins"
ovirthostdeployplugindir="\$(pkgdatadir)/plugins"
ovirthostdeploylibdir="\$(pythondir)/ovirt_host_deploy"
ovirthostdeployinterfacedir="\$(pkgdatadir)/interface-${INTERFACE_VERSION}"
AC_SUBST([otopiplugindir])
AC_SUBST([ovirthostdeployplugindir])
AC_SUBST([ovirthostdeploylibdir])
AC_SUBST([ovirthostdeployinterfacedir])
AC_SUBST([OTOPI_SOURCES])
AM_CONDITIONAL([PYTHON_SYNTAX_CHECK], [test "${enable_python_syntax_check}" = "yes"])
AM_CONDITIONAL([JAVA_SDK], [test "${enable_java_sdk}" = "yes"])
AM_CONDITIONAL([JAVA_SDK_COMPILE], [test "${enable_java_sdk_compile}" = "yes"])
AM_CONDITIONAL([WITH_MAVEN], [test "${with_maven}" = "yes"])

AC_CONFIG_FILES([
	Makefile
	ovirt-host-deploy.spec
	build/Makefile
	po/Makefile.in
	src/Makefile
	src/bin/Makefile
	src/ovirt_host_deploy/Makefile
	src/ovirt_host_deploy/config.py
	src/plugins/Makefile
	src/plugins/ovirt-host-deploy/Makefile
	src/plugins/ovirt-host-deploy/core/Makefile
	src/plugins/ovirt-host-deploy/vdsm/Makefile
	src/plugins/ovirt-host-deploy/vdsmhooks/Makefile
	src/plugins/ovirt-host-deploy/tune/Makefile
	src/plugins/ovirt-host-deploy/node/Makefile
	src/plugins/ovirt-host-deploy/gluster/Makefile
	src/plugins/ovirt-host-deploy/openstack/Makefile
	src/java/Makefile
	src/java/pom.xml
	src/interface-3/Makefile
	conf.d/Makefile
	tests/Makefile
])
AC_CONFIG_FILES(
	[src/bin/ovirt-host-deploy],
	[chmod a+x src/bin/ovirt-host-deploy]
)
AC_OUTPUT
