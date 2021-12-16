#!/usr/bin/env python3
from __future__ import print_function

import build
import errno
import logging
import optparse
import os
import distro
import sys

RUBY_VERSION = build.ruby_requirements['ruby']
RVM_PATH = build.ruby_requirements['path']

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise

def install_rvm_and_ruby():
    cmd = 'curl -sSL https://rvm.io/mpapis.asc | sudo gpg --import -'
    build.run_cmd(cmd, unsafe_shell=True, check_rc='curl failed')
    cmd = 'curl -sSL https://rvm.io/pkuczynski.asc | sudo gpg --import -'
    build.run_cmd(cmd, unsafe_shell=True, check_rc='curl failed')
    cmd = 'curl -sSL https://get.rvm.io | sudo bash -s stable'
    build.run_cmd(cmd, unsafe_shell=True, check_rc='curl failed')
    cmd = "sudo -E su -c '{rvm_path}/rvm reload && {rvm_path}/rvm requirements run && {rvm_path}/rvm install {ruby_version}'".format(
        ruby_version = RUBY_VERSION,
        rvm_path = RVM_PATH )
    build.run_cmd(cmd, unsafe_shell=True, run_env=True, check_rc='rvm ruby install failed')

def install_fpm_gem():
    build.set_ruby_path()
    cmd = """sudo -E su -c 'PATH="{PATH}"; export PATH; {rvm_path}/rvm reload && {rvm_path}/rvm use {ruby_version} && gem install -v 1.14.1 fpm'""".format(
        ruby_version = RUBY_VERSION,
        rvm_path = RVM_PATH,
        PATH = os.environ['PATH'] )
    build.run_cmd(cmd, unsafe_shell=True, run_env=True, check_rc='fpm gem install failed')


def main():
    # configure parser
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbose', action="count", dest='verbosity', default=1, help='print more information to stdout')
    parser.add_option('-q', '--quiet', action='store_const', const=0, dest='verbosity', help='print less information to stdout')
    parser.add_option('-p', '--package', action='store_true', dest='package', default=True)
    parser.add_option('-n', '--no-package', action='store_false', dest='package')
    (options, args) = parser.parse_args()

    # configure logging
    log = logging.getLogger()
    if options.verbosity >= 2:
        log.setLevel(logging.DEBUG)
    elif options.verbosity == 1:
        log.setLevel(logging.INFO)
    else:
        log.setLevel(logging.WARNING)
    ch = logging.StreamHandler()
    formatter = logging.Formatter("%(levelname)s - %(message)s")
    ch.setFormatter(formatter)
    log.addHandler(ch)

    distro_id = distro.id()
    distro_major_version = distro.major_version()

    if distro_id in ['debian', 'ubuntu']:
        log.info('Detected: {0}'.format(distro_id))
        cmd = ['sudo', 'apt-get', 'update', '-y']
        build.run_cmd(cmd, check_rc='getting updates failed')
        # get prerequisites
        cmd = ['sudo','DEBIAN_FRONTEND=noninteractive','apt-get','install','-y','curl','automake','make',
               'autoconf2.13','texinfo','help2man','git','gpg','lsb-release','libtool','libbz2-dev',
               'zlib1g-dev','libcurl4-gnutls-dev','libxml2-dev','pkg-config','python3-dev','uuid-dev',
               'libssl-dev','fuse','libfuse2','libfuse-dev', 'libmicrohttpd-dev', 'unixodbc-dev']
        if distro_id in ['debian']:
            # Debian 11's default GCC is version 10.2.
            # Debian containers do not have "ps" command by default.
            cmd.extend(['g++', 'procps']) 
        # At this point, we know we're dealing with some version of Ubuntu.
        elif distro_major_version == '20':
            # Compiling LLVM 13's libcxx requires at least GCC 10.
            cmd.extend(['gcc-10', 'g++-10']) 
        else:
            # Ubuntu 18 does not have any issues compiling LLVM 13's libcxx
            # because it is using GCC 7 which does not support any C++20 features.
            cmd.append('g++')
        build.run_cmd(cmd, check_rc='installing prerequisites failed')
        cmd = ['sudo','apt-get','install','-y','autoconf','rsync']
        build.run_cmd(cmd, check_rc='installing autoconf failed')
        cmd = ['sudo','apt-get','install','-y','patchelf']
        build.run_cmd(cmd, check_rc='installing patchelf failed')

    elif distro_id in ['rocky', 'almalinux', 'centos', 'rhel', 'scientific']:
        log.info('Detected: {0}'.format(distro_id))
        # prep
        if distro_id in ['rocky', 'almalinux']:
            cmd = ['sudo', 'dnf', 'install', '-y', 'epel-release', 'dnf-plugins-core']
            build.run_cmd(cmd, check_rc='rpm dnf install failed')
            cmd = ['sudo', 'dnf', 'config-manager', '--set-enabled', 'powertools']
            build.run_cmd(cmd, check_rc='rpm dnf config-manager failed')
            cmd = ['sudo', 'dnf', 'install', '-y', 'procps', 'redhat-lsb-core', 'rsync'] # For ps, lsb_release, and rsync.
            build.run_cmd(cmd, check_rc='yum install failed')
        else:
            cmd = ['sudo', 'rpm', '--rebuilddb']
            build.run_cmd(cmd, check_rc='rpm rebuild failed')
        cmd = ['sudo','yum','clean','all']
        build.run_cmd(cmd, check_rc='yum clean failed')
        if distro_id not in ['rocky', 'almalinux']:
            cmd = ['sudo','yum','install','centos-release-scl-rh', '-y']
            build.run_cmd(cmd, check_rc='yum install failed')
        cmd = ['sudo','yum','update','-y','glibc*','yum*','rpm*','python*']
        build.run_cmd(cmd, check_rc='yum update failed')
        # get prerequisites
        cmd = ['sudo','yum','install','-y','epel-release','wget','openssl','ca-certificates']
        build.run_cmd(cmd, check_rc='installing epel failed')
        cmd = ['sudo','yum','install','-y','curl','gcc-c++','git','autoconf','automake','texinfo',
               'help2man','rpm-build','rubygems','ruby-devel','zlib-devel','fuse','fuse-devel',
               'bzip2-devel','libcurl-devel','libmicrohttpd-devel','libxml2-devel','libtool','libuuid-devel','openssl-devel','unixODBC-devel','patchelf']
        if distro_id in ['rocky', 'almalinux']:
            cmd.append('python36-devel') # python39-devel also available.
        else:
            cmd.append('python3-devel')
        build.run_cmd(cmd, check_rc='installing prerequisites failed')

    elif distro_id in ['opensuse ', 'sles']:
        log.info('Detected: {0}'.format(distro_id))
        # get prerequisites
        cmd = ['sudo','zypper','install','-y','curl','tar','gzip','git','ruby-devel','libmicrohttpd-devel','makeinfo','rubygems',
               'libopenssl-devel','rpm-build','help2man','python-devel','libbz2-devel','libcurl-devel','libxml2-devel','libtool',
               'libuuid-devel','uuid-devel','unixODBC-devel','cyrus-sasl','patchelf']
        build.run_cmd(cmd, check_rc='installing prerequisites failed')
    else:
        if platform.mac_ver()[0] != '':
            log.info('Detected: {0}'.format(platform.mac_ver()[0]))
            # get prerequisites
            cmd = ['brew','install','git','help2man','texinfo','libtool']
            build.run_cmd(cmd, check_rc='installing prerequisites failed')
            cmd = ['brew','link','texinfo','--force']
            build.run_cmd(cmd, check_rc='linking texinfo failed')
        else:
            log.error('Cannot determine prerequisites for platform [{0}]'.format(distro_id))
            return 1

    # get necessary ruby gems
    if options.package:
        install_rvm_and_ruby()
        install_fpm_gem()

if __name__ == '__main__':
    sys.exit(main())
