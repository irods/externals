#!/bin/bash -x

COMMITISH=release_37
PACKAGE_NAME=clang
PACKAGE_VERSION=3.7
PACKAGE_LICENSE=LLVM
CONSORTIUM_BUILD_NUMBER=0
EXTERNALS_ROOT=opt/irods-externals

# variable math
SCRIPTPATH=$( cd $(dirname $0) ; pwd -P )
PACKAGE_SUBDIRECTORY=${PACKAGE_NAME}${PACKAGE_VERSION}-${CONSORTIUM_BUILD_NUMBER}
BUILDDIR=${SCRIPTPATH}/${PACKAGE_SUBDIRECTORY}_src
INSTALL_PREFIX=${BUILDDIR}/${EXTERNALS_ROOT}/${PACKAGE_SUBDIRECTORY}

# llvm
mkdir -p $BUILDDIR/build
cd $BUILDDIR
git clone https://github.com/irods/llvm
cd $BUILDDIR/llvm
git pull
git checkout $COMMITISH

# clang
cd $BUILDDIR/llvm/tools
git clone https://github.com/irods/clang
cd $BUILDDIR/llvm/tools/clang
git pull
git checkout $COMMITISH

# clang-tools-extra
cd $BUILDDIR/llvm/tools/clang/tools
git clone https://github.com/irods/clang-tools-extra
cd $BUILDDIR/llvm/tools/clang/tools/clang-tools-extra
git pull
git checkout $COMMITISH

# compiler-rt
cd $BUILDDIR/llvm/projects/
git clone https://github.com/irods/compiler-rt
cd $BUILDDIR/llvm/projects/compiler-rt
git pull
git checkout $COMMITISH

# libcxx
cd $BUILDDIR/llvm/projects/
git clone https://github.com/irods/libcxx
cd $BUILDDIR/llvm/projects/libcxx
git pull
git checkout $COMMITISH

# libcxx
cd $BUILDDIR/llvm/projects/
git clone https://github.com/irods/libcxxabi
cd $BUILDDIR/llvm/projects/libcxxabi
git pull
git checkout $COMMITISH

# build
cd $BUILDDIR/build
cmake -G "Unix Makefiles" -DCMAKE_BUILD_TYPE=Release -DCMAKE_INSTALL_PREFIX=$INSTALL_PREFIX ../llvm
make -j35
make install

# make packages
cd $SCRIPTPATH
fpm -f -s dir -t deb \
 -n irods-externals-${PACKAGE_SUBDIRECTORY} \
 -m "<packages@irods.org>" \
 --vendor "iRODS Consortium" \
 --license $PACKAGE_LICENSE \
 --description "iRODS Build Dependency" \
 --url "https://irods.org" \
 -C $BUILDDIR \
 ${EXTERNALS_ROOT}/${PACKAGE_SUBDIRECTORY}/bin \
 ${EXTERNALS_ROOT}/${PACKAGE_SUBDIRECTORY}/include \
 ${EXTERNALS_ROOT}/${PACKAGE_SUBDIRECTORY}/lib \
 ${EXTERNALS_ROOT}/${PACKAGE_SUBDIRECTORY}/share
