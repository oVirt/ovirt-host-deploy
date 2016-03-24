#!/bin/bash -e
autoreconf -ivf
./configure --enable-java-sdk
make distcheck
