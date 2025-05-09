#!/usr/bin/env python3
from __future__ import print_function

import errno
import itertools
import json
import logging
import multiprocessing
import optparse
import os
import re
import subprocess
import sys
from shutil import which

import distro_info

script_path = os.path.dirname(os.path.realpath(__file__))

ruby_requirements = {
    'ruby': '3.1.2',
    'path': '/usr/local/rvm/bin'
}

def touch(filename):
    try:
        os.utime(filename, None)
    except:
        open(filename, 'a').close()

def get_rvm_path():
    cmd = ['whereis', 'rvm']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _out, _err = p.communicate()
    index = len(_out.lstrip().split(b': ')) - 1
    rvm_path = _out.lstrip().split(b': ')[index]
    return rvm_path.strip().decode('utf-8')

def set_environ_path(bin_path):
    path = os.environ['PATH']
    new_path = bin_path + ':' + path
    os.environ['PATH'] = new_path

def set_rvm_path():
    rvm_path = get_rvm_path()
    rvm_bin = os.path.join(rvm_path, 'bin')
    set_environ_path(rvm_bin)

def set_ruby_path():
    rvm_path = '/usr/local/rvm'
    ruby_path = os.path.join(rvm_path, 'rubies/ruby-'+ruby_requirements['ruby'])
    ruby_bin = os.path.join(ruby_path, 'bin')
    os.environ['GEM_HOME'] = ruby_path
    set_environ_path(ruby_bin)

def set_clang_path():
    p = get_versions()['clang']
    path_name = '{0}{1}-{2}'.format('clang', p['version_string'], p['consortium_build_number'])
    externals_path = os.path.dirname(os.path.dirname(os.getcwd()))
    clang_binpath = os.path.join(externals_path, path_name, 'bin')
    set_environ_path(clang_binpath)

def get_local_path(package_name, path_elements):
    log = logging.getLogger(__name__)
    p = get_versions()[package_name]
    path_name = '{0}{1}-{2}'.format(package_name, p['version_string'], p['consortium_build_number'])
    local_path = os.path.join(script_path, '{0}_src'.format(path_name), p['externals_root'], path_name, *path_elements)
    log.debug('local path: {0}'.format(local_path))
    return local_path

def run_cmd(cmd, run_env=False, unsafe_shell=False, check_rc=False, retries=0):
    log = logging.getLogger(__name__)
    # run it
    if run_env == True:
        set_rvm_path()

    run_env = os.environ.copy()
    log.debug('run_env: {0}'.format(run_env))
    log.info('running: {0}, unsafe_shell={1}, check_rc={2}, retries={3}'.format(cmd, unsafe_shell, check_rc, retries))
    if unsafe_shell == True:
        p = subprocess.Popen(cmd, env=run_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    else:
        p = subprocess.Popen(cmd, env=run_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    log.info('  stdout: {0}'.format(out.strip().decode('utf-8')))
    log.info('  stderr: {0}'.format(err.strip().decode('utf-8')))
    log.info('')
    if check_rc != False:
        if p.returncode != 0:
            log.error(check_rc)
            if retries > 0:
                reduced_retries = retries - 1
                log.info('trying again with retries={0}'.format(reduced_retries))
                run_cmd(cmd, run_env=run_env, unsafe_shell=unsafe_shell, check_rc=check_rc, retries=reduced_retries)
            else:
                sys.exit(p.returncode)
    return p.returncode

def get_package_name(p):
    v = get_versions()[p]
    return 'irods-externals-{0}{1}-{2}'.format(p, v['version_string'], v['consortium_build_number'])

def get_package_version(p):
    # At present, all our package versions are 1.0.
    # This method is provided to make changing that easier, should we ever need to.
    return '1.0'

def get_package_revision(p):
    v = get_versions()[p]
    ver_pkgrev = v.get('package_revision', '0')
    ver_pkgrev_suffix1 = ''
    ver_pkgrev_suffix2 = ''
    if distro_info.package_filename_extension() == 'deb':
        ver_pkgrev_suffix1 = '~'
        ver_pkgrev_suffix2 = distro_info.distribution_codename()
    else:
        dt = distro_info.distribution_type()
        dv = distro_info.distribution_version()
        ver_pkgrev_suffix2 = str(dv)
        ver_pkgrev_suffix2 = dv
        if dt == 'rhel':
            ver_pkgrev_suffix1 = '.el'
        elif dt == 'fedora':
            ver_pkgrev_suffix1 = '.fc'
        else:
            # probably suse
            ver_pkgrev_suffix1 = '.{0}'.format(dt)
    return '{0}{1}{2}'.format(ver_pkgrev, ver_pkgrev_suffix1, ver_pkgrev_suffix2)

def get_package_filename(p):
    n = get_package_name(p)
    a = distro_info.package_architecture_string()
    t = distro_info.package_filename_extension()
    v = get_package_version(p)
    r = get_package_revision(p)
    if t == 'rpm':
        package_filename_template = '{0}-{1}-{2}.{3}.{4}'
    else:
        package_filename_template = '{0}_{1}-{2}_{3}.{4}'
    return package_filename_template.format(n, v, r, a, t)

def get_versions():
    with open(script_path + '/versions.json', 'r') as f:
        return json.load(f)

def get_package_dependencies(v):
    log = logging.getLogger(__name__)
    deps = []

    # dependencies on other externals packages
    if 'interdependencies' in v:
        for d in v['interdependencies']:
            deps.append(get_package_name(d))

    # distro-specific dependencies
    if 'distro_dependencies' in v:
        distro_type = distro_info.distribution_type()
        v_distro_deps = v['distro_dependencies']
        if distro_type in v_distro_deps:
            distro_ver = str(distro_info.distribution_version())
            distro_type_deps = v_distro_deps[distro_type]
            if distro_ver in distro_type_deps:
                deps.extend(distro_type_deps[distro_ver])
            else:
                log.debug('version [%s] of distro [%s] not in distro_dependencies', distro_ver, distro_type)
        else:
            log.debug('distro [%s] not in distro_dependencies', distro_type)

    return deps

def get_jobs():
    log = logging.getLogger(__name__)
    detected = int(multiprocessing.cpu_count())
    if detected > 1:
        using = detected - 1
    else:
        using = detected
    log.debug('{0} processor(s) detected, using -j{1}'.format(detected, using))
    return using

def build_package(target, build_native_package):
    log = logging.getLogger(__name__)
    print('Building [{0}]'.format(target))
    # prepare paths
    v = get_versions()[target]
    package_subdirectory = '{0}{1}-{2}'.format(target, v['version_string'], v['consortium_build_number'])
    build_dir = os.path.join(script_path, '{0}_src'.format(package_subdirectory))
    install_prefix = os.path.join(build_dir, v['externals_root'], package_subdirectory)
    log.info(install_prefix)

    def apply_patches():
        if 'patches' not in v:
            return
        patch_dir = os.path.join(script_path, 'patches')
        for patch in v['patches']:
            log.info(f'Applying patch [{patch}]')
            patch_path = os.path.join(patch_dir, patch)
            patch_cmd = ['patch', '-Nt', '-p1', '-i', patch_path]
            run_cmd(patch_cmd, check_rc='failed to apply patch (patch may be partially applied)')

    # prepare executables
    os.chdir(os.path.join(script_path))
    python_executable = sys.executable
    log.debug('python_executable: [{0}]'.format(python_executable))
    cmake_executable = get_local_path('cmake',['bin','cmake'])
    log.debug('cmake_executable: [{0}]'.format(cmake_executable))

    # prepare libraries
    cppzmq_root = get_local_path('cppzmq',[])
    log.debug('cppzmq_root: [{0}]'.format(cppzmq_root))
    avro_root = get_local_path('avro',[])
    log.debug('avro_root: [{0}]'.format(avro_root))
    boost_root = get_local_path('boost',[])
    log.debug('boost_root: [{0}]'.format(boost_root))
    fmt_root = get_local_path('fmt',[])
    log.debug('fmt_root: [{0}]'.format(fmt_root))
    json_root = get_local_path('json',[])
    log.debug('json_root: [{0}]'.format(json_root))

    # build boost install path
    boost_info = get_versions()['boost']
    boost_subdirectory = '{0}{1}-{2}'.format('boost', boost_info['version_string'], boost_info['consortium_build_number'])
    boost_install_prefix = os.path.join(boost_info['externals_root'], boost_subdirectory)
    boost_rpath = os.path.join(boost_install_prefix, 'lib')

    fmt_info = get_versions()['fmt']
    fmt_subdirectory = '{0}{1}-{2}'.format('fmt', fmt_info['version_string'], fmt_info['consortium_build_number'])
    fmt_install_prefix = os.path.join(fmt_info['externals_root'], fmt_subdirectory)
    fmt_rpath = os.path.join(fmt_install_prefix, 'lib')

    avro_info = get_versions()['avro']
    avro_subdirectory = '{0}{1}-{2}'.format('avro', avro_info['version_string'], avro_info['consortium_build_number'])
    avro_install_prefix = os.path.join(avro_info['externals_root'], avro_subdirectory)
    avro_rpath = os.path.join(avro_install_prefix, 'lib')

    clang_info = get_versions()['clang']
    clang_subdirectory = '{0}{1}-{2}'.format('clang', clang_info['version_string'], clang_info['consortium_build_number'])
    clang_executable = os.path.join(script_path, '{0}'.format(clang_subdirectory), 'bin', 'clang')
    clangpp_executable = os.path.join(script_path, '{0}'.format(clang_subdirectory), 'bin', 'clang++')
    clang_cpp_headers = os.path.join(script_path, '{0}'.format(clang_subdirectory), 'include', 'c++', 'v1')
    clang_cpp_libraries = os.path.join(script_path, '{0}'.format(clang_subdirectory), 'lib')

    qpid_proton_info = get_versions()['qpid-proton']
    qpid_proton_subdirectory = '{0}{1}-{2}'.format('qpid-proton', qpid_proton_info['version_string'], qpid_proton_info['consortium_build_number'])
    qpid_proton_install_prefix = os.path.join(qpid_proton_info['externals_root'], qpid_proton_subdirectory)
    qpid_proton_rpath = os.path.join(qpid_proton_install_prefix, 'lib')

    clang_gcc_install_prefix = os.getenv('IRODS_EXTERNALS_GCC_PREFIX', default='')

    # get and patch
    if target == 'clang':
        target_dir = os.path.join(build_dir, "llvm-project")
        if not os.path.isdir(os.path.join(build_dir, "build")):
            os.makedirs(os.path.join(build_dir, "build"))
        if not os.path.isdir(target_dir):
            os.chdir(build_dir)
            log.debug('cwd: {0}'.format(os.getcwd()))
            # Clone only the version we want! It would take too long to download all of LLVM.
            run_cmd(['git', 'clone', '--depth', '1', '--branch', v['commitish'], 'https://github.com/irods/llvm-project'])
            os.chdir('llvm-project')
            log.debug('cwd: {0}'.format(os.getcwd()))
            run_cmd(['git', 'fetch'], check_rc='git fetch failed')
            run_cmd(['git', 'checkout', v['commitish']], check_rc='git checkout failed')
            apply_patches()
    else:
        target_dir = os.path.join(build_dir, target)

        # Because cloning is disabled when the target directory exists, users who want to rebuild
        # a package using a different repository or commit must run "make <target>_clean" first.
        if not os.path.isdir(target_dir):
            os.makedirs(build_dir)
            os.chdir(build_dir)
            log.debug('cwd: {0}'.format(os.getcwd()))

            git_repository = v['git_repository'] if 'git_repository' in v else 'https://github.com/irods/{0}'.format(target)
            git_cmd = ['git', 'clone', '--recurse-submodules']

            # If the user defined "enable_sha" as true, clone the repository and then fetch/checkout
            # the commit of interest.
            if 'enable_sha' in v and v['enable_sha'] == True:
                git_cmd.append(git_repository)
                git_cmd.append(target)
                run_cmd(git_cmd, check_rc='git clone failed')
                os.chdir(target_dir)
                run_cmd(['git', 'fetch'], check_rc='git fetch failed')
                run_cmd(['git', 'checkout', v['commitish']], check_rc='git checkout failed')
            else:
                git_cmd.extend(['--depth', '1', '--branch', v['commitish']])
                git_cmd.append(git_repository)
                git_cmd.append(target)
                run_cmd(git_cmd, check_rc='git clone failed')
                os.chdir(target_dir)
            apply_patches()

    # set environment
    if target == 'boost':
        set_clang_path()

    myenv = os.environ.copy()
    if target not in ['clang','cmake']:
        clang_bindir = get_local_path('clang',['bin'])
        myenv['CC'] = '{0}/clang'.format(clang_bindir)
        log.debug('CC='+myenv['CC'])
        myenv['CXX'] = '{0}/clang++'.format(clang_bindir)
        log.debug('CXX='+myenv['CXX'])
        myenv['PATH'] = '{0}:{1}'.format(clang_bindir, myenv['PATH'])
        log.debug('PATH='+myenv['PATH'])

    # build
    if target == 'clang':
        os.chdir(os.path.join(build_dir, "llvm-project"))
    else:
        os.chdir(os.path.join(build_dir,target))

    for i in itertools.chain(v['build_steps'], v['external_build_steps']):
        i = re.sub("TEMPLATE_JOBS", str(get_jobs()), i)
        i = re.sub("TEMPLATE_SCRIPT_PATH", script_path, i)
        i = re.sub("TEMPLATE_INSTALL_PREFIX", install_prefix, i)
        i = re.sub("TEMPLATE_GCC_INSTALL_PREFIX", clang_gcc_install_prefix, i)
        i = re.sub("TEMPLATE_CLANG_CPP_HEADERS", clang_cpp_headers, i)
        i = re.sub("TEMPLATE_CLANG_CPP_LIBRARIES", clang_cpp_libraries, i)
        i = re.sub("TEMPLATE_CLANG_SUBDIRECTORY", clang_subdirectory, i)
        i = re.sub("TEMPLATE_CLANG_EXECUTABLE", clang_executable, i)
        i = re.sub("TEMPLATE_CLANGPP_EXECUTABLE", clangpp_executable, i)
        i = re.sub("TEMPLATE_CMAKE_EXECUTABLE", cmake_executable, i)
        i = re.sub("TEMPLATE_QPID_PROTON_SUBDIRECTORY", qpid_proton_subdirectory, i)
        i = re.sub("TEMPLATE_QPID_PROTON_RPATH", qpid_proton_rpath, i)
        i = re.sub("TEMPLATE_PYTHON_EXECUTABLE", python_executable, i)
        i = re.sub("TEMPLATE_BOOST_ROOT", boost_root, i)
        i = re.sub("TEMPLATE_BOOST_RPATH", boost_rpath, i)
        i = re.sub("TEMPLATE_AVRO_RPATH", avro_rpath, i)
        i = re.sub("TEMPLATE_AVRO_PATH", avro_root, i)
        i = re.sub("TEMPLATE_CPPZMQ_PATH", cppzmq_root, i)
        i = re.sub("TEMPLATE_FMT_PATH", fmt_root, i)
        i = re.sub("TEMPLATE_FMT_RPATH", fmt_rpath, i)
        i = re.sub("TEMPLATE_JSON_PATH", json_root, i)
        run_cmd(i, run_env=myenv, unsafe_shell=True, check_rc='build failed')

    # package
    if not build_native_package:
        return

    fpmbinary = 'fpm'
    fpmbinary = which(fpmbinary)
    if fpmbinary is None:
        log.error('fpm not found, try "gem install fpm"')
        sys.exit(1)
    os.chdir(script_path)
    package_cmd = [fpmbinary, '-f', '-s', 'dir']
    package_cmd.extend(['-t', distro_info.package_type()])
    package_cmd.extend(['-n', 'irods-externals-{0}'.format(package_subdirectory)])
    for d in get_package_dependencies(v):
        package_cmd.extend(['-d', d])
    package_cmd.extend(['-m', '<packages@irods.org>'])
    package_cmd.extend(['--version', get_package_version(target)])
    package_cmd.extend(['--iteration', get_package_revision(target)])
    package_cmd.extend(['--vendor', 'iRODS Consortium'])
    package_cmd.extend(['--license', v['license']])
    package_cmd.extend(['--description', 'iRODS Build Dependency'])
    package_cmd.extend(['--url', 'https://irods.org'])
    package_cmd.extend(['-C', build_dir])
    for i in sorted(v['fpm_directories']):
        addpath = os.path.join(v['externals_root'], package_subdirectory, i)
        # lib and lib64 might both be necessary for cross-platform builds
        if i.startswith("lib"):
            fullpath  = os.path.abspath(os.path.join(install_prefix, i))
            if os.path.isdir(fullpath):
                package_cmd.extend([addpath])
            else:
                log.debug("skipped ["+fullpath+"] (does not exist)")
        else:
            package_cmd.extend([addpath])
    if len(v['fpm_directories']) > 0:
        run_cmd(package_cmd, check_rc='packaging failed')
    else:
        touch(get_package_filename(target))
    print('Building [{0}] ... Complete'.format(target))

def main():
    # check parameters
    usage = "Usage: %prog [options] <target>"
    parser = optparse.OptionParser(usage)
    parser.add_option('-v', '--verbose', action="count", dest='verbosity', default=1, help='print more information to stdout')
    parser.add_option('-q', '--quiet', action='store_const', const=0, dest='verbosity', help='print less information to stdout')
    parser.add_option('-p', '--package', action='store_true', dest='package', default=True)
    parser.add_option('-n', '--no-package', action='store_false', dest='package')
    (options, args) = parser.parse_args()

    if len(args) == 0:
        parser.print_help()
        sys.exit(1)

    if len(args) != 1:
        parser.error("incorrect number of arguments")

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

    # build the target
    target = args[0]

    if target == 'packagesfile':
        v = get_versions()
        with open('packages.mk','w') as f:
            for p in v:
                f.write('{0}_PACKAGE={1}\n'.format(p.upper(), get_package_filename(p)))
    elif target in get_versions():
        set_rvm_path()
        set_ruby_path()
        build_package(target, options.package )
    else:
        log.error('build target [{0}] not found in {1}'.format(target, sorted(get_versions().keys())))
        return 1

if __name__ == '__main__':
    sys.exit(main())
