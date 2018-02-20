# External dependencies for the building and installation of iRODS

Currently tested on:

- Ubuntu 12
- Ubuntu 14
- Ubuntu 16
- CentOS 6
- CentOS 7
- OpenSUSE 13

# Installation

Before building the software listed in this repository, their own prerequisites must be met.

This is handled as automatically as possible with the `install_prerequisites.py` script.

```
./install_prerequisites.py
make
```

For CentOS 6, the included compilers are too old to build clang.

After the prerequisites are in place, make sure to use the newly installed g++.

```
./install_dependencies.py
export CC=/opt/rh/devtoolset-2/root/usr/bin/gcc
export CXX=/opt/rh/devtoolset-2/root/usr/bin/g++
make
```
