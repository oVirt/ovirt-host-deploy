#!/bin/bash -xe
[[ -d exported-artifacts ]] \
|| mkdir -p exported-artifacts

[[ -d tmp.repos ]] \
|| mkdir -p tmp.repos

SUFFIX=".$(date -u +%Y%m%d%H%M%S).git$(git rev-parse --short HEAD)"

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

autoreconf -ivf
./configure
yum-builddep ovirt-host-deploy.spec
# Run rpmbuild, assuming the tarball is in the project's directory
rpmbuild \
    -D "_topdir $PWD/tmp.repos" \
    -D "release_suffix ${SUFFIX}" \
    -ta ovirt-host-deploy-*.tar.gz

mv *.tar.gz exported-artifacts
find \
    "$PWD/tmp.repos" \
    -iname \*.rpm \
    -exec mv {} exported-artifacts/ \;
