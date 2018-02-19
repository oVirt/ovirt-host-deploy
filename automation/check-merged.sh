#!/bin/bash -e
# workaround for bad caching on slaves
yum --disablerepo=* --enablerepo=otopi-master-last-build clean metadata
yum -y install otopi-devtools

autoreconf -ivf
./configure --enable-java-sdk
make distcheck
