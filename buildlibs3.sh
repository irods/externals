#!/bin/bash -ex

COMMITISH=11a4e976
PACKAGE_NAME=libs3
PACKAGE_VERSION=11a4e976
PACKAGE_LICENSE="LGPL v3"
CONSORTIUM_BUILD_NUMBER=0
EXTERNALS_ROOT=opt/irods-externals

CLANG_BINARY=/opt/irods-externals/bin/clang

# variable math
SCRIPTPATH=$( cd $(dirname $0) ; pwd -P )
PACKAGE_SUBDIRECTORY=${PACKAGE_NAME}${PACKAGE_VERSION}-${CONSORTIUM_BUILD_NUMBER}
BUILDDIR=${SCRIPTPATH}/${PACKAGE_SUBDIRECTORY}_src
INSTALL_PREFIX=${BUILDDIR}/${EXTERNALS_ROOT}/${PACKAGE_SUBDIRECTORY}
export CC=$CLANG_BINARY
export CXX=${CLANG_BINARY}++

# get
mkdir -p $BUILDDIR
cd $BUILDDIR
if [ ! -d "$BUILDDIR/$PACKAGE_NAME" ] ; then git clone https://github.com/irods/$PACKAGE_NAME; fi
cd $BUILDDIR/$PACKAGE_NAME
git fetch
git checkout $COMMITISH

# build
cd $BUILDDIR/$PACKAGE_NAME
CFLAGS=-fPIC make -j35
make DESTDIR=$INSTALL_PREFIX install

# make packages
cd $SCRIPTPATH
fpm -f -s dir -t deb \
 -n irods-externals-${PACKAGE_SUBDIRECTORY} \
 -m '<packages@irods.org>' \
 --vendor 'iRODS Consortium' \
 --license "$PACKAGE_LICENSE" \
 --description 'iRODS Build Dependency' \
 --url 'https://irods.org' \
 -C $BUILDDIR \
 ${EXTERNALS_ROOT}/${PACKAGE_SUBDIRECTORY}/bin \
 ${EXTERNALS_ROOT}/${PACKAGE_SUBDIRECTORY}/lib \
 ${EXTERNALS_ROOT}/${PACKAGE_SUBDIRECTORY}/include
