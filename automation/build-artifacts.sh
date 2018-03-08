#!/bin/bash -xe
[[ -d exported-artifacts ]] \
|| mkdir -p exported-artifacts

[[ -d tmp.repos ]] \
|| mkdir -p tmp.repos


DISTVER="$(rpm --eval "%dist"|cut -c2-3)"
PACKAGER=""
if [[ "${DISTVER}" == "el" ]]; then
    PACKAGER=yum
else
    PACKAGER=dnf
fi

# workaround for bad caching on slaves
${PACKAGER} --disablerepo=* --enablerepo=otopi-4.2-last-build clean metadata
${PACKAGER} -y install otopi-devtools

autoreconf -ivf
./configure
make dist
yum-builddep ovirt-host-deploy.spec
rpmbuild \
    -D "_topdir $PWD/tmp.repos" \
    -ta ovirt-host-deploy-*.tar.gz

mv *.tar.gz exported-artifacts
find \
    "$PWD/tmp.repos" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;
