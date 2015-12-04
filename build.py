#!/usr/bin/env python
from __future__ import print_function

DEBUG = False
DEBUG = True

import os
import re
import sys
import json
import errno
import platform
import subprocess
import multiprocessing

script_path = os.path.dirname(os.path.realpath(__file__))

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def print_debug(msg):
    if DEBUG == True:
        print('DEBUG: {0}'.format(msg))

def print_error(msg):
    print('ERROR: {0}'.format(msg))

def get_local_path(package_name, path_elements):
    p = get_versions()[package_name]
    path_name = '{0}{1}-{2}'.format(package_name, p['version_string'], p['consortium_build_number'])
    local_path = os.path.join(script_path, '{0}_src'.format(path_name), p['externals_root'], path_name, *path_elements)
#    print_debug('local path: {0}'.format(local_path))
    return local_path

def run_cmd(cmd, run_env=False, unsafe_shell=False, check_rc=False):
    # run it
    if run_env == False:
        run_env = os.environ.copy()
    print_debug('run_env: {0}'.format(run_env))
    print_debug('running: {0}, unsafe_shell={1}, check_rc={2}'.format(cmd, unsafe_shell, check_rc))
    if unsafe_shell == True:
        p = subprocess.Popen(cmd, env=run_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE, shell=True)
    else:
        p = subprocess.Popen(cmd, env=run_env, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (out, err) = p.communicate()
    print_debug('  stdout: {0}'.format(out.strip()))
    print_debug('  stderr: {0}'.format(err.strip()))
    print_debug('')
    if check_rc != False:
        if p.returncode != 0:
            print_error(check_rc)
            sys.exit(p.returncode)
    return p.returncode

def get_package_filename(p):
    v = get_versions()[p]
    a = get_package_arch()
    t = get_package_type()
    if t == 'rpm':
        package_filename_template = 'irods-externals-{0}{1}-{2}-1.0-1.{4}.{3}'
    elif t == 'osxpkg':
        t = 'pkg'
        package_filename_template = 'irods-externals-{0}{1}-{2}-1.0.{3}'
    else:
        package_filename_template = 'irods-externals-{0}{1}-{2}_1.0_{4}.{3}'
    f = package_filename_template.format(p, v['version_string'], v['consortium_build_number'], t, a)
    return f

def get_versions():
    with open(script_path+'/versions.json','r') as f:
        return json.load(f)

def get_package_arch():
    a = platform.uname()[4]
    if get_package_type() == 'deb' and a == 'x86_64':
        return 'amd64'
    return a

def get_package_type():
    pld = platform.linux_distribution()[0]
#    print_debug('linux distribution detected: {0}'.format(pld))
    if pld in ['debian', 'Ubuntu']:
        pt = 'deb'
    elif pld in ['CentOS', 'CentOS Linux', 'Red Hat Enterprise Linux Server', 'openSUSE ', 'SUSE Linux Enterprise Server']:
        pt = 'rpm'
    else:
        if platform.mac_ver()[0] != '':
            pt = 'osxpkg'
        else:
            pt = 'not_detected'
#    print_debug('package type detected: {0}'.format(pt))
    return pt

def get_jobs():
    detected = int(multiprocessing.cpu_count())
    if detected > 1:
        using = detected - 1
    else:
        using = detected
    print_debug('{0} processor(s) detected, using -j{1}'.format(detected, using))
    return using

def build_package(target):
    # prepare paths
    v = get_versions()[target]
    package_subdirectory = '{0}{1}-{2}'.format(target, v['version_string'], v['consortium_build_number'])
    build_dir = os.path.join(script_path, '{0}_src'.format(package_subdirectory))
    install_prefix = os.path.join(build_dir, v['externals_root'], package_subdirectory)
    print_debug(install_prefix)

    # prepare executables
    os.chdir(os.path.join(script_path))
    if sys.version_info < (2, 7):
        python_executable = get_local_path('cpython',['bin','python2.7'])
    else:
        python_executable = sys.executable
        if target == 'cpython':
            print_debug('skipping cpython ... current python version {0} >= 2.7'.format(platform.python_version()))
            # touch file to satisfy make
            f = get_package_filename(target)
            with open(f, 'a'):
                os.utime(f, None)
            return
    print_debug('python_executable: [{0}]'.format(python_executable))
    cmake_executable = get_local_path('cmake',['bin','cmake'])
    print_debug('cmake_executable: [{0}]'.format(cmake_executable))

    # prepare libraries
    boost_root = get_local_path('boost',[])
    print_debug('boost_root: [{0}]'.format(boost_root))

    # prepare other strings
    if get_package_type() == 'osxpkg':
        libs3_makefile_string = '-f GNUmakefile.osx'
    else:
        libs3_makefile_string = ''
    print_debug('libs3_makefile_string: [{0}]'.format(libs3_makefile_string))

    # build boost install path
    boost_info = get_versions()['boost']
    boost_subdirectory = '{0}{1}-{2}'.format('boost', boost_info['version_string'], boost_info['consortium_build_number'])
    boost_install_prefix = os.path.join(boost_info['externals_root'], boost_subdirectory)
    boost_rpath = os.path.join(boost_install_prefix, 'lib')

    # get
    if target == 'clang':
        if not os.path.isdir(os.path.join(build_dir,"build")):
            mkdir_p(os.path.join(build_dir,"build"))
        target_dirs = [
                ('llvm', 'llvm'),
                ('clang', 'llvm/tools/clang'),
                ('clang-tools-extra', 'llvm/tools/clang/tools/clang-tools-extra'),
                ('compiler-rt', 'llvm/projects/compiler-rt'),
                ('libcxx', 'llvm/projects/libcxx'),
                ('libcxxabi', 'llvm/projects/libcxxabi')
            ]
        for t in target_dirs:
            if not os.path.isdir(os.path.join(build_dir,t[1])):
                mkdir_p(os.path.dirname(os.path.join(build_dir,t[1])))
                os.chdir(os.path.dirname(os.path.join(build_dir,t[1])))
                print_debug('cwd: {0}'.format(os.getcwd()))
                run_cmd(['git', 'clone', 'https://github.com/irods/{0}'.format(t[0])])
            os.chdir(os.path.join(build_dir,t[1]))
            print_debug('cwd: {0}'.format(os.getcwd()))
            run_cmd(['git', 'fetch'], check_rc='git fetch failed')
            run_cmd(['git', 'checkout', v['commitish']], check_rc='git checkout failed')
    else:
        if not os.path.isdir(os.path.join(build_dir,target)):
            mkdir_p(build_dir)
            os.chdir(build_dir)
            print_debug('cwd: {0}'.format(os.getcwd()))
            if target == 'boost':
                # using boostorg namespace instead of forking 50+ relatively linked submodules
                run_cmd(['git', 'clone', 'https://github.com/boostorg/boost'])
            else:
                run_cmd(['git', 'clone', 'https://github.com/irods/{0}'.format(target)])
        os.chdir(os.path.join(build_dir,target))
        run_cmd(['git', 'fetch'], check_rc='git fetch failed')
        run_cmd(['git', 'checkout', v['commitish']], check_rc='git checkout failed')

    # set environment
    myenv = os.environ.copy()
    if target not in ['clang','cmake','autoconf','cpython']:
        clang_bindir = get_local_path('clang',['bin'])
        myenv['CC'] = '{0}/clang'.format(clang_bindir)
#       print_debug('CC='+myenv['CC'])
        myenv['CXX'] = '{0}/clang++'.format(clang_bindir)
#       print_debug('CXX='+myenv['CXX'])
        myenv['PATH'] = '{0}:{1}'.format(clang_bindir, myenv['PATH'])
#       print_debug('PATH='+myenv['PATH'])
        autoconf_bindir = get_local_path('autoconf',['bin'])
        myenv['PATH'] = '{0}:{1}'.format(autoconf_bindir, myenv['PATH'])
#       print_debug('PATH='+myenv['PATH'])
    if get_package_type() == 'osxpkg' and target in ['jansson','zeromq4-1']:
        myenv['LIBTOOLIZE'] = 'glibtoolize'
#       print_debug('LIBTOOLIZE='+myenv['LIBTOOLIZE'])

    # build
    if target == 'clang':
        os.chdir(os.path.join(build_dir,"build"))
    else:
        os.chdir(os.path.join(build_dir,target))
    for i in v['build_steps']:
        i = re.sub("TEMPLATE_JOBS", str(get_jobs()), i)
        i = re.sub("TEMPLATE_SCRIPT_PATH", script_path, i)
        i = re.sub("TEMPLATE_INSTALL_PREFIX", install_prefix, i)
        i = re.sub("TEMPLATE_CMAKE_EXECUTABLE", cmake_executable, i)
        i = re.sub("TEMPLATE_PYTHON_EXECUTABLE", python_executable, i)
        i = re.sub("TEMPLATE_BOOST_ROOT", boost_root, i)
        i = re.sub("TEMPLATE_LIBS3_MAKEFILE_STRING", libs3_makefile_string, i)
        i = re.sub("TEMPLATE_BOOST_RPATH", boost_rpath, i)
        run_cmd(i, run_env=myenv, unsafe_shell=True, check_rc='build failed')

    for i in v['external_build_steps']:
        i = re.sub("TEMPLATE_JOBS", str(get_jobs()), i)
        i = re.sub("TEMPLATE_SCRIPT_PATH", script_path, i)
        i = re.sub("TEMPLATE_INSTALL_PREFIX", install_prefix, i)
        i = re.sub("TEMPLATE_CMAKE_EXECUTABLE", cmake_executable, i)
        i = re.sub("TEMPLATE_PYTHON_EXECUTABLE", python_executable, i)
        i = re.sub("TEMPLATE_BOOST_ROOT", boost_root, i)
        i = re.sub("TEMPLATE_LIBS3_MAKEFILE_STRING", libs3_makefile_string, i)
        i = re.sub("TEMPLATE_BOOST_RPATH", boost_rpath, i)
        run_cmd(i, run_env=myenv, unsafe_shell=True, check_rc='build failed')

    # MacOSX - after building boost
    # libraries lack an absolute path in their install_name, so apps using them fail to load
    # in our case, avro
    # https://svn.boost.org/trac/boost/ticket/9141
    if get_package_type() == 'osxpkg' and target == 'boost':
        run_cmd('for x in {0}/lib/*.dylib; do \
            install_name_tool -id $x $x; \
            install_name_tool -change libboost_system.dylib {0}/lib/libboost_system.dylib $x; \
            done'.format(boost_root), run_env=myenv, unsafe_shell=True, check_rc='osx dylib fullpath fix failed')

    # package
    if get_package_type() == 'osxpkg':
        print('MacOSX Detected - Skipping Package Build')
        # touch file to satisfy make
        f = get_package_filename(target)
        with open(os.path.join(script_path,f), 'a'):
            os.utime(f, None)
    else:
        if platform.linux_distribution()[0] == 'openSUSE ':
            fpmbinary='fpm.ruby2.1'
        else:
            fpmbinary='fpm'
        run_cmd(['which', fpmbinary], check_rc='fpm not found, try "gem install fpm"')
        os.chdir(script_path)
        package_cmd = [fpmbinary, '-f', '-s', 'dir']
        package_cmd.extend(['-t', get_package_type()])
        package_cmd.extend(['-n', 'irods-externals-{0}'.format(package_subdirectory)])
        package_cmd.extend(['-m', '<packages@irods.org>'])
        package_cmd.extend(['--vendor', 'iRODS Consortium'])
        package_cmd.extend(['--license', v['license']])
        package_cmd.extend(['--description', 'iRODS Build Dependency'])
        package_cmd.extend(['--url', 'https://irods.org'])
        package_cmd.extend(['-C', build_dir])
        if platform.linux_distribution()[0] == 'openSUSE ' and target in ['jansson','zeromq4-1']:
            v['fpm_directories'] = ['lib64' if x == 'lib' else x for x in v['fpm_directories']]
        for i in sorted(v['fpm_directories']):
            package_cmd.extend([os.path.join(v['externals_root'], package_subdirectory, i)])
        run_cmd(package_cmd, check_rc='packaging failed')
        print('Building [{0}] ... Complete'.format(target))

def main(target):
    if target == 'packagesfile':
        v = get_versions()
        with open('packages.mk','w') as f:
            for p in v:
                f.write('{0}_PACKAGE={1}\n'.format(p.upper(), get_package_filename(p)))
    elif target in get_versions():
        build_package(target)
    else:
        print_error('build target [{0}] not found in {1}'.format(target, sorted(get_versions().keys())))
        return 1

if __name__ == '__main__':
    if len(sys.argv) > 2:
        print('Usage: {0}'.format(__file__))
        print('Usage: {0} <target>'.format(__file__))
        sys.exit(1)

    if len(sys.argv) == 2:
        rc = main(sys.argv[1])
    else:
        rc = main()

    sys.exit(rc)

