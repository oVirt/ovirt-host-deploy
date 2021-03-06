#!/bin/bash -ex

DISTVER="$(rpm --eval "%dist"|cut -c2-4)"
PACKAGER=""
if [[ "${DISTVER}" == "el7" ]]; then
    PACKAGER=yum
else
    PACKAGER=dnf
fi

# workaround for bad caching on slaves
${PACKAGER} --disablerepo=* --enablerepo=otopi-master-last-tested clean metadata
${PACKAGER} -y install python2-otopi-devtools || echo "python2-otopi-devtools not found"
${PACKAGER} -y install python3-otopi-devtools || echo "python3-otopi-devtools not found"

if [[ $(rpm --eval "%{fedora}") -gt 29 ]] ; then
export PYTHON=python3
fi

autoreconf -ivf
./configure --enable-java-sdk
make distcheck

automation/build-artifacts.sh

# install otopi from latest jenkins before restoring yum environment
${PACKAGER} -y install "otopi*"

#Restoring sane yum environment
rm -f /etc/yum.conf
${PACKAGER} reinstall -y system-release ${PACKAGER}
[[ -d /etc/dnf ]] && [[ -x /usr/bin/dnf ]] && dnf -y reinstall dnf-conf
[[ -d /etc/dnf ]] && sed -i -re 's#^(reposdir *= *).*$#\1/etc/yum.repos.d#' '/etc/dnf/dnf.conf'
if [[ "${DISTVER}" == "el7" ]]; then
# on 4.4 we support deploying el7 hosts bue we are not providing el7 packages for 4.4 hosts.
# Using 4.3 repos instead.
${PACKAGER} install -y https://resources.ovirt.org/pub/yum-repo/ovirt-release43-snapshot.rpm
else
${PACKAGER} install -y ovirt-release-master
fi
rm -f /etc/yum/yum.conf

${PACKAGER} repolist enabled

${PACKAGER} install -y $(find "$PWD/exported-artifacts" -iname \*noarch\*.rpm)

if [[ "${DISTVER}" == "el7" ]]; then
# Fedora and EL 8 support is known to be broken, will be re-enabled once fixed

save_logs() {
mkdir -p exported-artifacts/logs
cp -p /tmp/ovirt-host-deploy-* exported-artifacts/logs
}

trap save_logs EXIT

rm -f /tmp/coverage.rc
cp "${PWD}/automation/coverage.rc" /tmp/
export COVERAGE_PROCESS_START="/tmp/coverage.rc"
export COVERAGE_FILE=$(mktemp -p $PWD .coverage.XXXXXX)
export OTOPI_DEBUG=1
export OTOPI_COVERAGE=1

automation/functional.expect

unset COVERAGE_FILE
coverage combine
coverage html -d exported-artifacts/coverage_html_report
cp automation/index.html exported-artifacts/

fi

