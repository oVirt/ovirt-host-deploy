#!/bin/bash -e
DISTVER="$(rpm --eval "%dist"|cut -c2-3)"
PACKAGER=""
if [[ "${DISTVER}" == "el" ]]; then
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
