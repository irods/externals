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

        main_package_list = [
            'autoconf',
            'automake',
            'bzip2-devel',
            'curl',
            'fuse',
            'fuse-devel',
            'gcc',
            'gcc-c++',
            'git',
            'glibc-devel',
            'help2man',
            'libcurl-devel',
            'libmicrohttpd-devel',
            'libtool',
            'libuuid-devel',
            'libxml2-devel',
            'openssl-devel',
            'patchelf',
            'python3-devel',
            'rpm-build',
            'ruby-devel',
            'rubygems',
            'texinfo',
            'unixODBC-devel',
            'zlib-devel'
        ]

        if distro_id in ['rocky', 'almalinux']:
            cmd = ['sudo', 'dnf', 'install', '-y', 'epel-release', 'dnf-plugins-core']
            build.run_cmd(cmd, check_rc='rpm dnf install failed')
            codeready_repo_name = 'powertools' if int(distro_major_version) < 9 else 'crb'
            cmd = ['sudo', 'dnf', 'config-manager', '--set-enabled', codeready_repo_name]
            build.run_cmd(cmd, check_rc='rpm dnf config-manager failed')
            cmd = ['sudo', 'dnf', 'install', '-y', 'procps', 'rsync'] # For ps and rsync.
            # lsb_release package appears to not be available in versions of EL 9 and on(?).
            if int(distro_major_version) < 9:
                cmd.append('redhat-lsb-core')
            build.run_cmd(cmd, check_rc='dnf install failed')
            cmd = ['sudo','dnf','clean','all']
            build.run_cmd(cmd, check_rc='dnf clean failed')
            cmd = ['sudo','dnf','install','-y','epel-release','wget','openssl','ca-certificates']
            build.run_cmd(cmd, check_rc='installing epel failed')
            cmd = ['sudo','dnf','install','-y']
            if int(distro_major_version) == 9:
                # For version 9, curl is installed by another step of this process and manually installing the package
                # here creates a conflict. Just delete curl from the list of packages to install.
                main_package_list.remove('curl')
            if int(distro_major_version) == 8:
                main_package_list.extend([
                    'gcc-toolset-11-gcc',
                    'gcc-toolset-11-gcc-c++',
                    'gcc-toolset-11-libstdc++-devel'
                ])
            build.run_cmd(cmd + main_package_list, check_rc='installing prerequisites failed')

        else:
            cmd = ['sudo', 'rpm', '--rebuilddb']
            build.run_cmd(cmd, check_rc='rpm rebuild failed')
            cmd = ['sudo','yum','clean','all']
            build.run_cmd(cmd, check_rc='yum clean failed')
            cmd = ['sudo','yum','install','centos-release-scl', '-y']
            build.run_cmd(cmd, check_rc='yum install failed')
            cmd = ['sudo','yum','install','-y','epel-release','wget','openssl','ca-certificates']
            build.run_cmd(cmd, check_rc='installing epel failed')
            main_package_list.extend([
                'devtoolset-10-gcc',
                'devtoolset-10-gcc-c++',
                'devtoolset-10-libstdc++-devel'
            ])
            cmd = ['sudo','yum','install','-y']
            build.run_cmd(cmd + main_package_list, check_rc='installing prerequisites failed')

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
