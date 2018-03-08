#!/bin/bash -e
DISTVER="$(rpm --eval "%dist"|cut -c2-3)"
PACKAGER=""
if [[ "${DISTVER}" == "el" ]]; then
    PACKAGER=yum
else
    PACKAGER=dnf
fi

# workaround for bad caching on slaves
${PACKAGER} --disablerepo=* --enablerepo=otopi-master-last-build clean metadata
${PACKAGER} -y install otopi-devtools

autoreconf -ivf
./configure --enable-java-sdk
make distcheck
