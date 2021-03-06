#!/bin/bash
##
## Deployment script for MadeiraCloud OpsAgent
## @author: Thibault BRONCHAIN
##
## (c) 2014 MadeiraCloud LTD.
##


USAGE="$0 tree|release"

GPG_PRIVATE_PATH=${HOME}/.ssh/keys/madeira.gpg.private.key

SCRIPTS_DIR=scripts
CONF_DIR=conf
LIBS_DIR=libs
SOURCES_DIR=sources

BUILD_DIR=build
RELEASE_DIR=release
OPSAGENT_DIR=opsagent
MISC_DIR=misc


function tree() {
    # Clear (if any) and create build directory
    rm -rf ${BUILD_DIR}
    # Create agent build/release directory
    mkdir -p ${BUILD_DIR}/${OPSAGENT_DIR}/{$SCRIPTS_DIR,$CONF_DIR,$LIBS_DIR,$SOURCES_DIR}

    # Move to build directory
    cd ${BUILD_DIR}

    # Add License
    cp ../LICENSE ${OPSAGENT_DIR}/

    # Copy bootstrap scripts
    cp ../${SCRIPTS_DIR}/{bootstrap.sh,daemon.sh,kill.sh,update.sh} ${OPSAGENT_DIR}/${SCRIPTS_DIR}/
    # Copy standalone scripts
    cp ../${SCRIPTS_DIR}/{init.sh,userdata.sh,clean.sh,ud_init.sh,manual_update.sh} ./
    cp -f ../${SCRIPTS_DIR}/ud_init.sh ./userdata.sh
    if [ "${1}" != "" ]; then
        sed "s/OA_VERSION=.*/OA_VERSION='${1}'/" < ../${SCRIPTS_DIR}/init.sh > ./init.sh
    else
        cp ../${SCRIPTS_DIR}/init.sh ./
    fi
    # Copy service launcher
    cp ../${SCRIPTS_DIR}/daemon.sh ${OPSAGENT_DIR}/${SCRIPTS_DIR}/
    # Copy EPEL installer
    cp -r ../${LIBS_DIR}/epel ${OPSAGENT_DIR}/${LIBS_DIR}/
    # Copy virtualenv
    cp -r ../${LIBS_DIR}/virtualenv ${OPSAGENT_DIR}/${LIBS_DIR}/
    # Copy ws4py sources
    cp -r ../${LIBS_DIR}/ws4py ${OPSAGENT_DIR}/${LIBS_DIR}/
    # Copy salt dependencies
    cp -r ../${LIBS_DIR}/{requests,msgpack,yaml,jinja2,markupsafe} ${OPSAGENT_DIR}/${LIBS_DIR}/

    # Copy opsagent sources
    for file in `find ../${SOURCES_DIR}/opsagent -type f -name '*.py'`
    do
        dir=`echo ${file} | rev | cut -d '/' -f 2-100 | rev | cut -d '/' -f 3-100 -s`
        mkdir -p ${OPSAGENT_DIR}/${SOURCES_DIR}/${dir}
        cp -f ${file} "${OPSAGENT_DIR}/${SOURCES_DIR}/${dir}"
    done

    # Copy launcher script
    if [ "${1}" != "" ]; then
        sed "s/VERSION_NBR=.*/VERSION_NBR='${1}'/" < ../${SOURCES_DIR}/opsagent.py > ${OPSAGENT_DIR}/${SCRIPTS_DIR}/opsagent
        sed "s/VERSION=.*/VERSION='${1}'/" < ../${SCRIPTS_DIR}/init.sh > ${OPSAGENT_DIR}/${SCRIPTS_DIR}/init.sh
    else
        cp ../${SOURCES_DIR}/opsagent.py ${OPSAGENT_DIR}/${SCRIPTS_DIR}/opsagent
    fi

    # create tarball
    cd ${OPSAGENT_DIR}
    tar cvfz ../opsagent.tgz *
    cd -
}

function publish() {
    echo "${1}" > curent
    rm -rf ${RELEASE_DIR}
    mkdir -p ${RELEASE_DIR}

    cp ${BUILD_DIR}/{clean.sh,init.sh,ud_init.sh,opsagent.tgz,userdata.sh,manual_update.sh} ${RELEASE_DIR}/

    # GPG
    gpg --allow-secret-key-import --import ${GPG_PRIVATE_PATH}
    cd ${BUILD_DIR}
    gpg --sign init.sh
    gpg --sign ud_init.sh
    gpg --sign opsagent.tgz
    gpg --sign userdata.sh
    cd -
    cp -f ${BUILD_DIR}/{init.sh.gpg,opsagent.tgz.gpg,ud_init.sh.gpg,userdata.sh.gpg} ${RELEASE_DIR}/

    cd ${RELEASE_DIR}
    cksum clean.sh > clean.sh.cksum
    cksum manual_update.sh > manual_update.sh.cksum
    cksum userdata.sh > userdata.sh.cksum
    cksum userdata.sh.gpg > userdata.sh.gpg.cksum
    cksum init.sh > init.sh.cksum
    cksum init.sh.gpg > init.sh.gpg.cksum
    cksum ud_init.sh > ud_init.sh.cksum
    cksum ud_init.sh.gpg > ud_init.sh.gpg.cksum
    cksum opsagent.tgz > opsagent.tgz.cksum
    cksum opsagent.tgz.gpg > opsagent.tgz.gpg.cksum
    cd -

    cp ${MISC_DIR}/madeira.gpg.public.key ${RELEASE_DIR}/madeira.gpg.public.key
    git add . -A
    git commit -m "v${1}"
    git push
}

function update() {
    git add . -A
    git commit -m "${1}"
    git pull
}

function merge() {
    git checkout master
    git pull origin master
    git merge develop
    git push origin master
    git checkout develop
}

case $1 in
    tree)
        tree
        ;;
    release)
        git status
        echo
        echo
        echo -n "Please input commit message then [ENTER]: "
        read COMMIT
        echo -n "Please input release number [ENTER]: "
        read RELEASE_NAME
        ROOT=${PWD}
        update "${COMMIT}"
        cd ${ROOT}
        tree "${RELEASE_NAME}"
        cd ${ROOT}
        publish "${RELEASE_NAME}"
        echo -n "Merge to master? [y/N]: "
        read MERGE
        if [ "$MERGE" = "y" ]; then
            merge
        else
            echo "No"
        fi
        echo "Done."
        ;;
    *)
        echo -e "syntax error\nusage: $USAGE"
        ;;
esac
