# External dependencies for the building and installation of iRODS

Currently tested on:

- Ubuntu 18
- Ubuntu 20
- CentOS 7
- AlmaLinux 8
- Rocky Linux 8
- Debian 11

# Assumptions

This repository is expected to build in a VM or container environment that is isolated from other software or build environments.

The automated scripts run commands as `sudo` and update system libraries and compilers, etc.

In a new container, run the following:

## Ubuntu 18, Ubuntu 20, and Debian 11

```bash
apt-get update -y && apt-get install -y sudo git python3 python3-distro
./install_prerequisites.py
make # or "make server" for packages specific to building the iRODS server.
```

## CentOS 7

```bash
yum update -y && yum install -y sudo git python3 centos-release-scl
yum install -y devtoolset-10-gcc devtoolset-10-gcc-c++

# Installing the prerequistes must be done before enabling the GCC compiler
# environment.
python3 -m venv build_env
source build_env/bin/activate
python -m pip install distro
./install_prerequisites.py

# Enable the GCC 10 compiler tools.
scl enable devtoolset-10 bash

# Although it appears that the python virtual environment has been deactivated,
# trust and believe it is still active.
make # or "make server" for packages specific to building the iRODS server.
```

## AlmaLinux 8 and Rocky Linux 8

```bash
dnf update -y && dnf install -y sudo git python3 python3-distro
./install_prerequisites.py
make # or "make server" for packages specific to building the iRODS server.
```
