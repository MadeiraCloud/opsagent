#!/bin/bash
##
## Deployment script for MadeiraCloud OpsAgent
## Version 0.0.1a
## @author: Thibault BRONCHAIN
##
## (c) 2014 MadeiraCloud LTD.
##


VIRTUALENV_VERSION=1.9
BUILD_DIR=build
VIRTUALENV_URI=https://pypi.python.org/packages/source/v/virtualenv/virtualenv-${VIRTUALENV_VERSION}.tar.gz
WS4PY_URI=https://github.com/Lawouach/WebSocket-for-Python.git
CONF=test.cfg


# Clear (if any) and create build directory
rm -rf ${BUILD_DIR}
mkdir ${BUILD_DIR}
cd ${BUILD_DIR}
# Create agent build tree
mkdir -p madeira/{bootstrap,sources,env/etc}
# Fetch virtualenv
curl -O ${VIRTUALENV_URI}
tar xvfz virtualenv-${VIRTUALENV_VERSION}.tar.gz
# Create virtualenv directory in tree
mv virtualenv-${VIRTUALENV_VERSION} madeira/bootstrap/virtualenv
# Fetch ws4py library
git clone ${WS4PY_URI}
# Copy ws4py sources
cp -r WebSocket-for-Python/ws4py madeira/sources/
# Copy salt sources
cp -r ../salt madeira/sources/
# Copy opsagent sources
cp -r ../opsagent madeira/sources/
# Copy config files
cp ../conf/${CONF} madeira/env/etc/
