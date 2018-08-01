# External dependencies for the building and installation of iRODS

Currently tested on:

- Ubuntu 14
- Ubuntu 16
- Ubuntu 18
- CentOS 7

# Assumptions

This repository is expected to build in a VM or container environment that is isolated from other software or build environments.

The automated scripts run commands as `sudo` and update system libraries and compilers, etc.

# Installation

Before building the software listed in this repository, their own prerequisites must be met.

This is handled as automatically as possible with the `install_prerequisites.py` script.

```
./install_prerequisites.py
make
```
