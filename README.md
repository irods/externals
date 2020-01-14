# External dependencies for the building and installation of iRODS

Currently tested on:

- Ubuntu 14
- Ubuntu 16
- Ubuntu 18
- CentOS 7
- Debian 9

# Assumptions

This repository is expected to build in a VM or container environment that is isolated from other software or build environments.

The automated scripts run commands as `sudo` and update system libraries and compilers, etc.

In a new container, you'll probably need the following:

```
# Ubuntu 16
apt-get install -y sudo git python

# CentOS 7
yum install -y sudo git python
```

# Installation

Before building the software listed in this repository, their own prerequisites must be met.

This is handled as automatically as possible with the `install_prerequisites.py` script.

```
./install_prerequisites.py
make
```

To only build the components for the iRODS Server:
```
make server
```
