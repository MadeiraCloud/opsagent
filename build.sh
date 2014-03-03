#!/bin/bash
##
## Deployment script for MadeiraCloud OpsAgent
## @author: Thibault BRONCHAIN
##
## (c) 2014 MadeiraCloud LTD.
##


USAGE="$0 tree|release"

SCRIPTS_DIR=scripts
CONF_DIR=conf
LIBS_DIR=libs
SOURCES_DIR=sources

BUILD_DIR=build
RELEASE_DIR=release
OPSAGENT_DIR=opsagent


function tree() {
    # Clear (if any) and create build directory
    rm -rf ${BUILD_DIR}
    # Create agent build/release directory
    mkdir -p ${BUILD_DIR}/${OPSAGENT_DIR}/{$SCRIPTS_DIR,$CONF_DIR,$LIBS_DIR,$SOURCES_DIR}

    # move to build directory
    cd ${BUILD_DIR}

    # Copy bootstrap scripts
    cp ../${SCRIPTS_DIR}/bootstrap.sh ${OPSAGENT_DIR}/${SCRIPTS_DIR}/
    # Copy standalone scripts
    cp ../${SCRIPTS_DIR}/{init.sh,userdata.sh,clean.sh} ./
    cksum init.sh > init.cksum
    cksum userdata.sh > userdata.cksum
    cksum clean.sh > clean.cksum
    # TODO: remove
    # Copy unit tests
    cd ../POCs/salt
    tar cfz test.tgz test
    cd -
    mv ../POCs/salt/test.tgz ./
    cksum test.tgz > test.cksum
    # /TODO
    # Copy service launcher
    cp ../${SCRIPTS_DIR}/daemon.sh ${OPSAGENT_DIR}/${SCRIPTS_DIR}/
    # Copy EPEL installer
    cp -r ../${LIBS_DIR}/epel ${OPSAGENT_DIR}/${LIBS_DIR}/
    # Copy virtualenv
    cp -r ../${LIBS_DIR}/virtualenv ${OPSAGENT_DIR}/${LIBS_DIR}/
    # Copy ws4py sources
    cp -r ../${LIBS_DIR}/ws4py ${OPSAGENT_DIR}/${LIBS_DIR}/
    # Copy salt dependencies
    cp -r ../${LIBS_DIR}/{msgpack,yaml,jinja2,markupsafe} ${OPSAGENT_DIR}/${LIBS_DIR}/
#    cp -r ../${LIBS_DIR}/{msgpack,yaml,jinja2,markupsafe,salt} ${OPSAGENT_DIR}/${LIBS_DIR}/

    # Copy opsagent sources
    for file in `find ../${SOURCES_DIR}/opsagent -type f -name '*.py'`
    do
        dir=`echo ${file} | rev | cut -d '/' -f 2-100 | rev | cut -d '/' -f 3-100 -s`
        mkdir -p ${OPSAGENT_DIR}/${SOURCES_DIR}/${dir}
        cp -f ${file} "${OPSAGENT_DIR}/${SOURCES_DIR}/${dir}"
    done

    # Copy launcher script
    cp ../${SOURCES_DIR}/opsagent.py ${OPSAGENT_DIR}/${SCRIPTS_DIR}/opsagent

    # Copy config files
    cp ../${CONF_DIR}/opsagent.conf ${OPSAGENT_DIR}/${CONF_DIR}/

    # create tarball
    cd ${OPSAGENT_DIR}
    tar cvfz ../opsagent.tgz *
    cd -
    # generate checksum
    cksum opsagent.tgz > opsagent.cksum
}

function publish() {
    rm -rf ${RELEASE_DIR}
    mkdir -p ${RELEASE_DIR}
    cp ${BUILD_DIR}/{init.cksum,init.sh,opsagent.cksum,opsagent.tgz,userdata.cksum,userdata.sh} ${RELEASE_DIR}/
    git add . -A
    git commit -m "release ${1}"
    git pull
    git push
}

case $1 in
    tree)
        tree
        ;;
    release)
        echo -n "Please input release name then [ENTER]: "
        read RELEASE_NAME
        ROOT=${PWD}
        tree
        cd ${ROOT}
        publish "${RELEASE_NAME}"
        ;;
    *)
        echo -e "syntax error\nusage: $USAGE"
        ;;
esac
