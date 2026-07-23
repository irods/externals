#!/usr/bin/env python3
from __future__ import print_function

import errno
import logging
import optparse
import os
import distro
import sys
import urllib.request
from shutil import which
from tempfile import TemporaryDirectory
from textwrap import dedent

import build
import distro_info
from distro_info import DistroVersion

def main():
    # configure parser
    parser = optparse.OptionParser()
    parser.add_option('-v', '--verbose', action="count", dest='verbosity', default=1, help='print more information to stdout')
    parser.add_option('-q', '--quiet', action='store_const', const=0, dest='verbosity', help='print less information to stdout')
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
    distro_type = distro_info.distribution_type()
    distro_version = distro_info.distribution_version()

    log.info('Detected: {0} {1} ({2})'.format(distro_id, str(distro_version), distro_type))

    nfpm_path = which('nfpm')

    if distro_type in ['debian', 'ubuntu']:
        package_list = [
            'cmake',
            'curl',
            'fuse',
            'g++',
            'gcc',
            'git',
            'gpg',
            'help2man',
            'libarchive-dev',
            'libbz2-dev',
            'libcurl4-gnutls-dev',
            'libfmt-dev',
            'libfuse-dev',
            'libicu-dev',
            'liblzma-dev',
            'libmicrohttpd-dev',
            'libssl-dev',
            'libtool',
            'libxml2-dev',
            'libzmq3-dev',
            'libzstd-dev',
            'lsb-release',
            'make',
            'nlohmann-json3-dev',
            'patch',
            'procps',
            'pkg-config',
            'python3-dev',
            'python3-yaml',
            'rsync',
            'texinfo',
            'unixodbc-dev',
            'uuid-dev',
            'zlib1g-dev',
        ]

        apt_env = os.environ.copy()
        apt_env['DEBIAN_FRONTEND'] = 'noninteractive'

        # install ca-certificates first
        cmd = ['apt-get', 'update', '-y']
        build.run_cmd(cmd, check_rc='getting updates failed')

        cmd = ['apt-get', 'install', '-y', 'ca-certificates']
        build.run_cmd(cmd, run_env=apt_env, check_rc='installing ca-certificates failed')

        if distro_type == 'ubuntu':
            if distro_version >= DistroVersion('26.04'):
                package_list += ['gcc-14', 'g++-14', 'libcrypt-dev']

            elif distro_version == DistroVersion('22.04'):
                # nanodbc requires slightly newer version of cmake to build
                repo_list_path = '/etc/apt/sources.list.d/kitware.list'
                repo_pref_path = '/etc/apt/preferences.d/kitware-cmake-325'

                if not os.path.exists(repo_list_path):
                    with TemporaryDirectory(prefix='irods-kiware') as kitware_tmp:
                        kitware_keyring_deb = os.path.join(os.path.abspath(kitware_tmp), 'kitware-archive-keyring.deb')

                        urllib.request.urlretrieve(
                            'https://apt.kitware.com/ubuntu/pool/main/k/kitware-archive-keyring/kitware-archive-keyring_2026.06.22_all.deb',
                            kitware_keyring_deb
                        )
                        
                        cmd = ['apt-get', 'install', '-y', kitware_keyring_deb]
                        build.run_cmd(cmd, run_env=apt_env, check_rc='installing kitware keyring failed')

                    with open(repo_list_path, 'wt', encoding='utf-8') as repo_list:
                        repo_list.write(
                            'deb [signed-by=/usr/share/keyrings/kitware-archive-keyring.gpg] https://apt.kitware.com/ubuntu/ jammy main\n'
                        )

                    # we only want cmake (and updated keyrings) from this repo, so deprioritize everything else
                    # also, make sure we don't grab a cmake version that's too *new*
                    with open(repo_pref_path, 'wt', encoding='utf-8') as repo_pref:
                        repo_pref.write(dedent('''\
                            Package: *
                            Pin: origin apt.kitware.com
                            Pin-Priority: 400

                            Package: src:kitware-archive-keyring:any
                            Pin: origin apt.kitware.com
                            Pin-Priority: 550

                            Package: src:cmake:any
                            Pin: version 3.25.*
                            Pin-Priority: 500
                        '''))

                    # update kitware-archive-keyring first
                    cmd = ['apt-get', 'update', '-y']
                    build.run_cmd(cmd, check_rc='getting updates failed')

                    cmd = ['apt-get', 'install', '-y', 'kitware-archive-keyring']
                    build.run_cmd(cmd, run_env=apt_env, check_rc='updating kitware-archive-keyring failed')

        if nfpm_path is None:
            repo_list_path = '/etc/apt/sources.list.d/goreleaser.list'

            if not os.path.exists(repo_list_path):
                with open(repo_list_path, 'wt', encoding='utf-8') as repo_list:
                    repo_list.write('deb [trusted=yes] https://repo.goreleaser.com/apt/ /\n')

            package_list.extend(['nfpm'])

        cmd = ['apt-get', 'update', '-y']
        build.run_cmd(cmd, check_rc='getting updates failed')

        cmd = ['apt-get', 'install', '-y']
        build.run_cmd(cmd + package_list, run_env=apt_env, check_rc='installing prerequisites failed')

    elif distro_type in ['rhel', 'scientific']:
        package_list = [
            'bzip2-devel',
            'ca-certificates',
            'cmake',
            # Starting with EL9, curl is provided by curl-minimal by default.
            # We don't need the full package, so let's just ensure curl-minimal is installed.
            'curl-minimal',
            'fmt-devel',
            'fuse',
            'fuse-devel',
            'gcc',
            'gcc-c++',
            'git',
            'glibc-devel',
            'help2man',
            'libarchive-devel',
            'libcurl-devel',
            'libicu-devel',
            'libmicrohttpd-devel',
            'libtool',
            'libuuid-devel',
            'libxml2-devel',
            'libzstd-devel',
            'nlohmann_json-devel',
            'openssl',
            'openssl-devel',
            'patch',
            'procps',
            'python3-devel',
            'python3-pyyaml',
            'rpm-build',
            'rsync',
            'texinfo',
            'unixODBC-devel',
            'wget',
            'xz-devel',
            'zeromq-devel',
            'zlib-devel',
        ]

        cmd = ['dnf', 'clean', 'all']
        build.run_cmd(cmd, check_rc='dnf clean failed')

        cmd = ['dnf', 'install', '-y', 'epel-release', 'dnf-plugins-core']
        build.run_cmd(cmd, check_rc='dnf install repos failed')

        codeready_repo_name = 'powertools' if distro_version < DistroVersion('9') else 'crb'
        cmd = ['dnf', 'config-manager', '--set-enabled', codeready_repo_name]
        build.run_cmd(cmd, check_rc='dnf config-manager failed')

        if nfpm_path is None:
            yum_repo_path = '/etc/yum.repos.d/goreleaser.repo'

            if not os.path.exists(yum_repo_path):
                with open(yum_repo_path, 'wt', encoding='utf-8') as yum_repo:
                    yum_repo.write('[goreleaser]\n')
                    yum_repo.write('name=GoReleaser\n')
                    yum_repo.write('baseurl=https://repo.goreleaser.com/yum/\n')
                    yum_repo.write('enabled=1\n')
                    yum_repo.write('gpgcheck=0\n')

            package_list.extend(['nfpm'])

        cmd = ['dnf', 'install', '-y']
        build.run_cmd(cmd + package_list, check_rc='installing prerequisites failed')

    else:
        log.error('Cannot determine prerequisites for platform [{0}]'.format(distro_id))
        return 1

if __name__ == '__main__':
    sys.exit(main())
