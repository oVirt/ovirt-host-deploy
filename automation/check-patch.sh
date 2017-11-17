#!/bin/bash -ex

# workaround for bad caching on slaves
yum --disablerepo=* --enablerepo=otopi-4.2-last-build clean metadata
yum -y install otopi-devtools

autoreconf -ivf
./configure --enable-java-sdk
make distcheck

automation/build-artifacts.sh

# install otopi from latest jenkins before restoring yum environment
yum -y install "otopi*"

#Restoring sane yum environment
rm -f /etc/yum.conf
yum reinstall -y system-release yum
[[ -d /etc/dnf ]] && [[ -x /usr/bin/dnf ]] && dnf -y reinstall dnf-conf
[[ -d /etc/dnf ]] && sed -i -re 's#^(reposdir *= *).*$#\1/etc/yum.repos.d#' '/etc/dnf/dnf.conf'
yum install -y ovirt-release42-snapshot
rm -f /etc/yum/yum.conf

yum repolist enabled

yum install -y $(find "$PWD/exported-artifacts" -iname \*noarch\*.rpm)

DISTVER="$(rpm --eval "%dist"|cut -c2-3)"
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

