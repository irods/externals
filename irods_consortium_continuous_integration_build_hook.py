#!/usr/bin/python
from __future__ import print_function
import optparse
import os

import irods_python_ci_utilities

def copy_output_packages(build_directory, output_root_directory):
    irods_python_ci_utilities.gather_files_satisfying_predicate(
        build_directory,
        irods_python_ci_utilities.append_os_specific_directory(output_root_directory),
        lambda s:s.endswith(irods_python_ci_utilities.get_package_suffix()))

def main(output_root_directory):
    build_directory = os.getcwd()
    irods_python_ci_utilities.subprocess_get_output(['python', 'install_prerequisites.py'], check_rc=True, cwd=os.path.dirname(os.path.realpath(__file__)))
    irods_python_ci_utilities.subprocess_get_output(['make'], check_rc=True, cwd=os.path.dirname(os.path.realpath(__file__)))
    if output_root_directory:
        copy_output_packages(build_directory, output_root_directory)

if __name__ == '__main__':
    parser = optparse.OptionParser()
    parser.add_option('--output_root_directory')
    options, _ = parser.parse_args()

    main(options.output_root_directory)
