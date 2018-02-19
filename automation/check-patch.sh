#!/bin/bash -e
# workaround for bad caching on slaves
yum --disablerepo=* --enablerepo=otopi-4.2-last-build clean metadata
yum -y install otopi-devtools

autoreconf -ivf
./configure --enable-java-sdk
make distcheck

automation/build-artifacts.sh
