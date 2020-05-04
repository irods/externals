#!/usr/bin/env python
from __future__ import print_function

import errno
import itertools
import json
import logging
import multiprocessing
import optparse
import os
import platform
import re
import subprocess
import sys

script_path = os.path.dirname(os.path.realpath(__file__))

ruby_requirements = {
    'rvm': '2.6',
    'ruby': '2.6.5',
    'path': '/usr/local/rvm/bin'
}

def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc: # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else: raise

def touch(filename):
    try:
        os.utime(filename, None)
    except:
        open(filename, 'a').close()

def get_rvm_path():
    cmd = ['whereis', 'rvm']
    p = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    _out, _err = p.communicate()
    index = len(_out.lstrip().split(': ')) - 1
    rvm_path = _out.lstrip().split(': ')[index]
    return rvm_path.strip()

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
    log.info('  stdout: {0}'.format(out.strip()))
    log.info('  stderr: {0}'.format(err.strip()))
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

def get_distribution_name():
    log = logging.getLogger(__name__)
    cmd = ['lsb_release','-s','-c']
    p = subprocess.Popen(cmd, env=os.environ.copy(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    (d, err) = p.communicate()
    log.debug('linux distribution name detected: {0}'.format(d.strip()))
    return d.strip()

def get_package_filename(p):
    v = get_versions()[p]
    a = get_package_arch()
    t = get_package_type()
    d = ''
    if t == 'rpm':
        package_filename_template = 'irods-externals-{0}{1}-{2}-1.0-1.{4}.{3}'
    elif t == 'osxpkg':
        t = 'pkg'
        package_filename_template = 'irods-externals-{0}{1}-{2}-1.0.{3}'
    else:
        d = get_distribution_name()
        package_filename_template = 'irods-externals-{0}{1}-{2}_1.0~{5}_{4}.{3}'
    f = package_filename_template.format(p, v['version_string'], v['consortium_build_number'], t, a, d)
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
    log = logging.getLogger(__name__)
    pld = platform.linux_distribution()[0]
    log.debug('linux distribution detected: {0}'.format(pld))
    if pld in ['debian', 'Ubuntu']:
        pt = 'deb'
    elif pld in ['CentOS', 'CentOS Linux', 'Red Hat Enterprise Linux Server', 'Scientific Linux', 'openSUSE ', 'SUSE Linux Enterprise Server']:
        pt = 'rpm'
    else:
        if platform.mac_ver()[0] != '':
            pt = 'osxpkg'
        else:
            pt = 'not_detected'
    log.debug('package type detected: {0}'.format(pt))
    return pt

def get_jobs():
    log = logging.getLogger(__name__)
    detected = int(multiprocessing.cpu_count())
    if detected > 1:
        using = detected - 1
    else:
        using = detected
    log.debug('{0} processor(s) detected, using -j{1}'.format(detected, using))
    return using

def build_package(target):
    log = logging.getLogger(__name__)
    print('Building [{0}]'.format(target))
    # prepare paths
    v = get_versions()[target]
    package_subdirectory = '{0}{1}-{2}'.format(target, v['version_string'], v['consortium_build_number'])
    build_dir = os.path.join(script_path, '{0}_src'.format(package_subdirectory))
    install_prefix = os.path.join(build_dir, v['externals_root'], package_subdirectory)
    log.info(install_prefix)

    # prepare executables
    os.chdir(os.path.join(script_path))
    if sys.version_info < (2, 7):
        python_executable = get_local_path('cpython',['bin','python2.7'])
    else:
        python_executable = sys.executable
        if target == 'cpython':
            log.debug('skipping cpython ... current python version {0} >= 2.7'.format(platform.python_version()))
            # touch file to satisfy make
            touch(get_package_filename(target))
            return
    log.debug('python_executable: [{0}]'.format(python_executable))
    cmake_executable = get_local_path('cmake',['bin','cmake'])
    log.debug('cmake_executable: [{0}]'.format(cmake_executable))

    # prepare libraries
    cppzmq_root = get_local_path('cppzmq',[])
    log.debug('cppzmq_root: [{0}]'.format(cppzmq_root))
    zmq_root = get_local_path('zeromq4-1',[])
    log.debug('zmq_root: [{0}]'.format(zmq_root))
    avro_root = get_local_path('avro',[])
    log.debug('avro_root: [{0}]'.format(avro_root))
    boost_root = get_local_path('boost',[])
    log.debug('boost_root: [{0}]'.format(boost_root))

    # prepare other strings
    if get_package_type() == 'osxpkg':
        libs3_makefile_string = '-f GNUmakefile.osx'
    else:
        libs3_makefile_string = ''
    log.debug('libs3_makefile_string: [{0}]'.format(libs3_makefile_string))

    # build boost install path
    boost_info = get_versions()['boost']
    boost_subdirectory = '{0}{1}-{2}'.format('boost', boost_info['version_string'], boost_info['consortium_build_number'])
    boost_install_prefix = os.path.join(boost_info['externals_root'], boost_subdirectory)
    boost_rpath = os.path.join(boost_install_prefix, 'lib')

    avro_info = get_versions()['avro']
    avro_subdirectory = '{0}{1}-{2}'.format('avro', avro_info['version_string'], avro_info['consortium_build_number'])
    avro_install_prefix = os.path.join(avro_info['externals_root'], avro_subdirectory)
    avro_rpath = os.path.join(avro_install_prefix, 'lib')

    libarchive_info = get_versions()['libarchive']
    libarchive_subdirectory = '{0}{1}-{2}'.format('libarchive', libarchive_info['version_string'], libarchive_info['consortium_build_number'])
    libarchive_install_prefix = os.path.join(libarchive_info['externals_root'], libarchive_subdirectory)
    libarchive_rpath = os.path.join(libarchive_install_prefix, 'lib')

    zmq_info = get_versions()['zeromq4-1']
    zmq_subdirectory = '{0}{1}-{2}'.format('zeromq4-1', zmq_info['version_string'], zmq_info['consortium_build_number'])
    zmq_install_prefix = os.path.join(zmq_info['externals_root'], zmq_subdirectory)
    zmq_rpath = os.path.join(zmq_install_prefix, 'lib')

    cpr_info = get_versions()['cpr']
    cpr_subdirectory = '{0}{1}-{2}'.format('cpr', cpr_info['version_string'], cpr_info['consortium_build_number'])
    cpr_install_prefix = os.path.join(cpr_info['externals_root'], cpr_subdirectory)
    cpr_rpath = os.path.join(cpr_install_prefix, 'lib')

    clang_info = get_versions()['clang']
    clang_subdirectory = '{0}{1}-{2}'.format('clang', clang_info['version_string'], clang_info['consortium_build_number'])
    clang_executable = os.path.join(script_path, '{0}'.format(clang_subdirectory), 'bin', 'clang')
    clangpp_executable = os.path.join(script_path, '{0}'.format(clang_subdirectory), 'bin', 'clang++')
    clang_cpp_headers = os.path.join(script_path, '{0}'.format(clang_subdirectory), 'include', 'c++', 'v1')
    clang_cpp_libraries = os.path.join(script_path, '{0}'.format(clang_subdirectory), 'lib')

    clang_runtime_subdirectory = '{0}{1}-{2}'.format('clang-runtime', clang_info['version_string'], clang_info['consortium_build_number'])
    clang_runtime_install_prefix = os.path.join(clang_info['externals_root'], clang_runtime_subdirectory)
    clang_runtime_rpath = os.path.join(clang_runtime_install_prefix, 'lib')

    qpid_info = get_versions()['qpid']
    qpid_subdirectory = '{0}{1}-{2}'.format('qpid', qpid_info['version_string'], qpid_info['consortium_build_number'])
    qpid_install_prefix = os.path.join(qpid_info['externals_root'], qpid_subdirectory)
    qpid_rpath = os.path.join(qpid_install_prefix, 'lib')

    qpidproton_info = get_versions()['qpid-proton']
    qpidproton_subdirectory = '{0}{1}-{2}'.format('qpid-proton', qpidproton_info['version_string'], qpidproton_info['consortium_build_number'])
   
    # get
    if target == 'clang':
        if not os.path.isdir(os.path.join(build_dir,"build")):
            mkdir_p(os.path.join(build_dir,"build"))
        target_dirs = [
                ('llvm', 'llvm'),
                ('clang', 'llvm/tools/clang'),
                ('clang-tools-extra', 'llvm/tools/clang/tools/extra'),
                ('compiler-rt', 'llvm/projects/compiler-rt'),
                ('libcxx', 'llvm/projects/libcxx'),
                ('libcxxabi', 'llvm/projects/libcxxabi')
            ]
        for t in target_dirs:
            if not os.path.isdir(os.path.join(build_dir,t[1])):
                mkdir_p(os.path.dirname(os.path.join(build_dir,t[1])))
                os.chdir(os.path.dirname(os.path.join(build_dir,t[1])))
                log.debug('cwd: {0}'.format(os.getcwd()))
                run_cmd(['git', 'clone', 'https://github.com/irods/{0}'.format(t[0]),t[1].split("/")[-1]])
            os.chdir(os.path.join(build_dir,t[1]))
            log.debug('cwd: {0}'.format(os.getcwd()))
            run_cmd(['git', 'fetch'], check_rc='git fetch failed')
            run_cmd(['git', 'checkout', v['commitish']], check_rc='git checkout failed')
    elif target == 'clang-runtime':
        if not os.path.isdir(os.path.join(build_dir,target)):
            mkdir_p(os.path.join(build_dir, target))
    elif target == 'qpid-with-proton':
        if not os.path.isdir(os.path.join(build_dir,target)):
            mkdir_p(os.path.join(build_dir, target))
    else:
        if not os.path.isdir(os.path.join(build_dir,target)):
            mkdir_p(build_dir)
            os.chdir(build_dir)
            log.debug('cwd: {0}'.format(os.getcwd()))
            if target == 'boost':
                # using boostorg namespace instead of forking 50+ relatively linked submodules
                run_cmd(['git', 'clone', 'https://github.com/boostorg/boost'])
            else:
                run_cmd(['git', 'clone', 'https://github.com/irods/{0}'.format(target)])
        os.chdir(os.path.join(build_dir,target))
        run_cmd(['git', 'fetch'], check_rc='git fetch failed')
        run_cmd(['git', 'checkout', v['commitish']], check_rc='git checkout failed')

    # set environment
    if target == 'boost':
        set_clang_path()

    myenv = os.environ.copy()
    if target not in ['clang','cmake','autoconf','cpython']:
        clang_bindir = get_local_path('clang',['bin'])
        myenv['CC'] = '{0}/clang'.format(clang_bindir)
        log.debug('CC='+myenv['CC'])
        myenv['CXX'] = '{0}/clang++'.format(clang_bindir)
        log.debug('CXX='+myenv['CXX'])
        myenv['PATH'] = '{0}:{1}'.format(clang_bindir, myenv['PATH'])
        log.debug('PATH='+myenv['PATH'])
        autoconf_bindir = get_local_path('autoconf',['bin'])
        myenv['PATH'] = '{0}:{1}'.format(autoconf_bindir, myenv['PATH'])
        log.debug('PATH='+myenv['PATH'])
    if get_package_type() == 'osxpkg' and target in ['jansson','zeromq4-1']:
        myenv['LIBTOOLIZE'] = 'glibtoolize'
        log.debug('LIBTOOLIZE='+myenv['LIBTOOLIZE'])

    # build
    if target == 'clang':
        os.chdir(os.path.join(build_dir,"build"))
    else:
        os.chdir(os.path.join(build_dir,target))

    for i in itertools.chain(v['build_steps'], v['external_build_steps']):
        i = re.sub("TEMPLATE_JOBS", str(get_jobs()), i)
        i = re.sub("TEMPLATE_SCRIPT_PATH", script_path, i)
        i = re.sub("TEMPLATE_INSTALL_PREFIX", install_prefix, i)
        i = re.sub("TEMPLATE_CLANG_CPP_HEADERS", clang_cpp_headers, i)
        i = re.sub("TEMPLATE_CLANG_CPP_LIBRARIES", clang_cpp_libraries, i)
        i = re.sub("TEMPLATE_CLANG_SUBDIRECTORY", clang_subdirectory, i)
        i = re.sub("TEMPLATE_CLANG_EXECUTABLE", clang_executable, i)
        i = re.sub("TEMPLATE_CLANGPP_EXECUTABLE", clangpp_executable, i)
        i = re.sub("TEMPLATE_CLANG_RUNTIME_RPATH", clang_runtime_rpath, i)
        i = re.sub("TEMPLATE_CMAKE_EXECUTABLE", cmake_executable, i)
        i = re.sub("TEMPLATE_QPID_SUBDIRECTORY", qpid_subdirectory, i)
        i = re.sub("TEMPLATE_QPID-PROTON_SUBDIRECTORY", qpidproton_subdirectory, i)
        i = re.sub("TEMPLATE_PYTHON_EXECUTABLE", python_executable, i)
        i = re.sub("TEMPLATE_BOOST_ROOT", boost_root, i)
        i = re.sub("TEMPLATE_LIBS3_MAKEFILE_STRING", libs3_makefile_string, i)
        i = re.sub("TEMPLATE_BOOST_RPATH", boost_rpath, i)
        i = re.sub("TEMPLATE_LIBARCHIVE_RPATH", libarchive_rpath, i)
        i = re.sub("TEMPLATE_AVRO_RPATH", avro_rpath, i)
        i = re.sub("TEMPLATE_AVRO_PATH", avro_root, i)
        i = re.sub("TEMPLATE_CPR_RPATH", cpr_rpath, i)
        i = re.sub("TEMPLATE_QPID_RPATH", qpid_rpath, i)
        i = re.sub("TEMPLATE_ZMQ_RPATH", zmq_rpath, i)
        i = re.sub("TEMPLATE_ZMQ_PATH", zmq_root, i)
        i = re.sub("TEMPLATE_CPPZMQ_PATH", cppzmq_root, i)
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
        f = os.path.join(script_path,get_package_filename(target))
        touch(f)
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
        try:
            if get_package_type() == 'rpm' and v['rpm_dependencies']:
                for d in v['rpm_dependencies']:
                    package_cmd.extend(['-d', d])
        except KeyError:
            pass
        package_cmd.extend(['-m', '<packages@irods.org>'])
        if get_package_type() == 'deb':
            d = get_distribution_name()
            package_cmd.extend(['--version', '1.0~{0}'.format(d)])
        else:
            package_cmd.extend(['--version', '1.0'])
        package_cmd.extend(['--vendor', 'iRODS Consortium'])
        package_cmd.extend(['--license', v['license']])
        package_cmd.extend(['--description', 'iRODS Build Dependency'])
        package_cmd.extend(['--url', 'https://irods.org'])
        package_cmd.extend(['-C', build_dir])
        for i in sorted(v['fpm_directories']):
            addpath = os.path.join(v['externals_root'], package_subdirectory, i)
            # lib and lib64 might both be necessary for cross-platform builds
            if i.startswith("lib"):
                fullpath = os.path.abspath(os.path.join(build_dir,addpath))
                if os.path.isdir(fullpath):
                    package_cmd.extend([addpath])
                else:
                    log.debug("skipped fullpath=["+fullpath+"] (does not exist)")
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
        build_package(target)
    else:
        log.error('build target [{0}] not found in {1}'.format(target, sorted(get_versions().keys())))
        return 1

if __name__ == '__main__':
    sys.exit(main())
