#!/bin/bash -xe
[[ -d exported-artifacts ]] \
|| mkdir -p exported-artifacts

[[ -d tmp.repos ]] \
|| mkdir -p tmp.repos

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

SUFFIX=".$(date -u +%Y%m%d%H%M%S).git$(git rev-parse --short HEAD)"

if [[ $(rpm --eval "%{fedora}") -gt 29 ]] ; then
export PYTHON=python3
fi

autoreconf -ivf
./configure
make dist
yum-builddep ovirt-host-deploy.spec
rpmbuild \
    -D "_topdir $PWD/tmp.repos" \
    -D "release_suffix ${SUFFIX}" \
    -ta ovirt-host-deploy-*.tar.gz

mv *.tar.gz exported-artifacts
find \
    "$PWD/tmp.repos" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;
