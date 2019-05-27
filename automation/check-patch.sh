#!/bin/bash -ex

DISTVER="$(rpm --eval "%dist"|cut -c2-3)"
PACKAGER=""
if [[ "${DISTVER}" == "el" ]]; then
    PACKAGER=yum
else
    PACKAGER=dnf
fi

# workaround for bad caching on slaves
${PACKAGER} --disablerepo=* --enablerepo=otopi-43-last-tested clean metadata
${PACKAGER} -y install otopi-devtools

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
${PACKAGER} install -y ovirt-release43-snapshot
rm -f /etc/yum/yum.conf

# On EL7 enable Virt SIG testing repos
if [[ "${DISTVER}" == "el" ]]; then
${PACKAGER} install -y centos-release-ovirt43
sed -i "s:enabled=0:enabled=1:" /etc/yum.repos.d/CentOS-oVirt-4.3.repo
fi



${PACKAGER} repolist enabled

${PACKAGER} install -y $(find "$PWD/exported-artifacts" -iname \*noarch\*.rpm)

if [[ ! "${DISTVER}" == "fc" ]]; then
# Fedora support is known to be broken, will be re-enabled once fixed

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

