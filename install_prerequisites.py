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

    log.info('Detected: {0}'.format(distro_id))

    if distro_id in ['debian', 'ubuntu']:
        package_list = [
            'autoconf',
            'autoconf2.13',
            'automake',
            'curl',
            'fuse',
            'git',
            'gpg',
            'help2man',
            'libbz2-dev',
            'libcurl4-gnutls-dev',
            'libfuse-dev',
            'libmicrohttpd-dev',
            'libssl-dev',
            'libtool',
            'libxml2-dev',
            'lsb-release',
            'make',
            'patchelf',
            'procps',
            'pkg-config',
            'python3-dev',
            'rsync',
            'texinfo',
            'unixodbc-dev',
            'uuid-dev',
            'zlib1g-dev',
        ]

        cmd = ['sudo', 'apt-get', 'update', '-y']
        build.run_cmd(cmd, check_rc='getting updates failed')

        if distro_id == 'ubuntu' and distro_major_version == '20':
            # Compiling LLVM 13's libcxx doesn't work with GCC 9.
            package_list.extend(['gcc-10', 'g++-10'])
        else:
            package_list.extend(['gcc', 'g++'])

        cmd = ['sudo', 'DEBIAN_FRONTEND=noninteractive', 'apt-get', 'install', '-y']
        build.run_cmd(cmd + package_list, check_rc='installing prerequisites failed')

    elif distro_id in ['rocky', 'almalinux', 'centos', 'rhel', 'scientific']:
        package_list = [
            'autoconf',
            'automake',
            'bzip2-devel',
            'ca-certificates',
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
            'openssl',
            'openssl-devel',
            'patchelf',
            'procps',
            'python3-devel',
            'rpm-build',
            'rsync',
            'ruby-devel',
            'rubygems',
            'texinfo',
            'unixODBC-devel',
            'wget',
            'zlib-devel',
        ]

        if distro_id in ['rocky', 'almalinux']:
            cmd = ['sudo', 'dnf', 'clean', 'all']
            build.run_cmd(cmd, check_rc='dnf clean failed')

            cmd = ['sudo', 'dnf', 'install', '-y', 'epel-release', 'dnf-plugins-core']
            build.run_cmd(cmd, check_rc='dnf install repos failed')

            codeready_repo_name = 'powertools' if int(distro_major_version) < 9 else 'crb'
            cmd = ['sudo', 'dnf', 'config-manager', '--set-enabled', codeready_repo_name]
            build.run_cmd(cmd, check_rc='dnf config-manager failed')

            if int(distro_major_version) < 9:
                package_list.extend([
                    'curl',
                    'gcc-toolset-11-gcc',
                    'gcc-toolset-11-gcc-c++',
                    'gcc-toolset-11-libstdc++-devel',
                    'redhat-lsb-core',
                ])
            else:
                # Starting with EL9, curl is provided by curl-minimal by default.
                # We don't need the full package, so let's just ensure curl-minimal is installed.
                package_list.extend([
                    'curl-minimal',
                ])

            cmd = ['sudo', 'dnf', 'install', '-y']
            build.run_cmd(cmd + package_list, check_rc='installing prerequisites failed')

        else:
            cmd = ['sudo', 'rpm', '--rebuilddb']
            build.run_cmd(cmd, check_rc='rpm rebuild failed')
            cmd = ['sudo', 'yum', 'clean', 'all']
            build.run_cmd(cmd, check_rc='yum clean failed')

            cmd = ['sudo', 'yum', 'install', '-y', 'epel-release', 'centos-release-scl']
            build.run_cmd(cmd, check_rc='yum install repos failed')

            package_list.extend([
                'curl',
                'devtoolset-10-gcc',
                'devtoolset-10-gcc-c++',
                'devtoolset-10-libstdc++-devel',
            ])

            cmd = ['sudo', 'yum', 'install', '-y']
            build.run_cmd(cmd + package_list, check_rc='installing prerequisites failed')

    else:
        log.error('Cannot determine prerequisites for platform [{0}]'.format(distro_id))
        return 1

    # get necessary ruby gems
    if options.package:
        install_rvm_and_ruby()
        install_fpm_gem()

if __name__ == '__main__':
    sys.exit(main())
