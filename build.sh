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
BOOTSTRAP_DIR=bootstrap
BUILD_DIR=build
TREE_DIR=$BUILD_DIR/tree
USER_DIR=$BUILD_DIR/userdata
OA_ROOT="opsagent"

PYTHON_APT=python2.7
PYTHON_YUM=python27


function tree() {
    # Clear (if any) and create build directory
    rm -rf ${TREE_DIR}
    mkdir -p ${TREE_DIR}
    cd ${TREE_DIR}
    # Create agent build tree
    mkdir -p $OA_ROOT/{bootstrap,sources,env/etc,env/bin}
    # Copy bootstrap scripts
    cp ../../bootstrap/bootstrap_{apt,yum}.sh $OA_ROOT/bootstrap/
    # Copy services install scripts
    cp ../../bootstrap/bootstrap_{chkconfig,updaterc}.sh $OA_ROOT/bootstrap/
    # Copy services launchers
    cp ../../bootstrap/daemon.sh $OA_ROOT/bootstrap/
    # Copy virtualenv
    cp -r ../../libs/virtualenv $OA_ROOT/bootstrap/
    # Copy ws4py sources
    cp -r ../../libs/ws4py $OA_ROOT/sources/
    # Copy salt and dependencies
    cp -r ../../libs/{msgpack,yaml,jinja2,markupsafe,salt} $OA_ROOT/sources/
    # Patch salt
    cp -r ../../salt $OA_ROOT/sources/
    # Copy opsagent sources
    for file in `find ../../opsagent/opsagent -type f -name '*.py'`
    do
        dir=`echo ${file} | rev | cut -d '/' -f 2-100 | rev | cut -d '/' -f 4-100 -s`
        mkdir -p $OA_ROOT/sources/${dir}
        cp -f ${file} "$OA_ROOT/sources/${dir}"
    done
    # Copy launch script editing shebang
    sed -e "s/#!\/usr\/bin\/python/#!\/madeira\/env\/bin\/python/g" < ../../opsagent/opsagent.py > $OA_ROOT/env/bin/opsagent
    chmod +x $OA_ROOT/env/bin/opsagent
    # Copy config files
    cp ../../conf/* $OA_ROOT/env/etc/ #TODO change * to opsagent.conf
    tar cfvz ../agent.tgz $OA_ROOT
    cd ..
    CRC="$(cksum agent.tgz)"
    echo $CRC > agent.cksum
#    sed -e "s/%CRC%/${CRC}/g" < ${BOOTSTRAP_DIR}/bootstrap.tpl.sh > ${BOOTSTRAP_DIR}/bootstrap.sh
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
