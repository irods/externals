#!/bin/bash -ex

####### for out of date centos6

# fix clock skew
yum install -y ntpdate
ntpdate -s time.nist.gov
date

# upgrade to latest centos6
yum clean all
yum update -y glibc* yum* rpm* python*
yum update -y
# reboot

####### for centos6

# install epel
yum install -y epel-release wget
yum update -y

# development tools
#yum groupinstall -y "Development tools"
#yum install -y zlib-devel bzip2-devel openssl-devel ncurses-devel sqlite-devel
#yum install -y readline-devel tk-devel gdbm-devel db4-devel libpcap-devel xz-devel

# more development tools
wget http://ftp.mirrorservice.org/sites/ftp.scientificlinux.org/linux/scientific/51/i386/RPM-GPG-KEYs/RPM-GPG-KEY-cern
rpm --import RPM-GPG-KEY-cern
wget -O /etc/yum.repos.d/slc6-devtoolset.repo http://linuxsoft.cern.ch/cern/devtoolset/slc6-devtoolset.repo
yum install -y devtoolset-2
#scl enable devtoolset-2 bash

# use new compiler to build the things
export CC=/opt/rh/devtoolset-2/root/usr/bin/gcc
export CXX=/opt/rh/devtoolset-2/root/usr/bin/g++


####### for centos6 and centos7

# external dependencies

sudo yum install -y gcc-c++ autoconf automake texinfo help2man rpm-build rubygems ruby-devel python-devel zlib-devel bzip2-devel libcurl-devel libxml2-devel libtool

sudo gem install fpm
