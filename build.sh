#!/bin/bash
##
## Deployment script for MadeiraCloud OpsAgent
## Version 0.0.1a
## @author: Thibault BRONCHAIN
##
## (c) 2014 MadeiraCloud LTD.
##


USAGE="$0 tree | (userdata APT|YUM {app_id} {token} {instance_id})"

VIRTUALENV_VERSION=1.9
BUILD_DIR=build
TREE_DIR=$BUILD_DIR/tree
USER_DIR=$BUILD_DIR/userdata
VIRTUALENV_URI=https://pypi.python.org/packages/source/v/virtualenv/virtualenv-${VIRTUALENV_VERSION}.tar.gz
WS4PY_URI=https://github.com/Lawouach/WebSocket-for-Python.git
#CONF="{aws_test.cfg,madeira_test.cfg,test.cfg}"

PYTHON_APT=python2.7
PYTHON_YUM=python27


function tree() {
    # Clear (if any) and create build directory
    rm -rf ${TREE_DIR}
    mkdir -p ${TREE_DIR}
    cd ${TREE_DIR}
    # Create agent build tree
    mkdir -p madeira/{bootstrap,sources,env/etc,env/bin}
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
    cp -r ../../salt-0.17.4/salt madeira/sources/
    # Patch salt
    cp -r ../../salt madeira/sources/
    # Copy opsagent sources
    for file in `find ../../opsagent/opsagent -type f -name '*.py'`
    do
        dir=`echo ${file} | rev | cut -d '/' -f 2-100 | rev | cut -d '/' -f 4-100 -s`
        mkdir -p madeira/sources/${dir}
        cp -f ${file} "madeira/sources/${dir}"
    done
    # Copy launch script editing shebang
    sed -e "s/#!\/usr\/bin\/python/#!\/madeira\/env\/bin\/python/g" < ../../opsagent/opsagent.py > madeira/env/bin/opsagent
    chmod +x madeira/env/bin/opsagent
    # Copy config files
    cp ../../conf/*.cfg madeira/env/etc/
    tar cfvz ../agent.tgz madeira
}

function userdata() {
    mkdir -p ${USER_DIR}
    cd ${USER_DIR}
    MANAGER=$1
    APP_ID=$2
    TOKEN=$3
    IID=$4
    eval PYTHON_VERSION=\${PYTHON_$MANAGER}
    if [ $MANAGER = 'APT' ]; then
        ADD_PKG="  - python-apt"
    else
        ADD_PKG=""
    fi
    sed -e "s/%python%/${PYTHON_VERSION}/g" \
        -e "s/%app_id%/${APP_ID}/g" \
        -e "s/%token%/${TOKEN}/g" \
        -e "s/%add_pkg%/${ADD_PKG}/g" \
        < ../../bootstrap.yaml > bootstrap_$IID.yaml
}


case $1 in
    tree)
        tree
        ;;
    userdata)
        userdata $2 $3 $4 $5
        ;;
    *)
        echo -e "syntax error\nusage: $USAGE"
        ;;
esac
