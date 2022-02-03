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

# The following lines apply to Ubuntu 20 only!!!
update-alternatives --install /usr/local/bin/gcc gcc /usr/bin/gcc-10 1
update-alternatives --install /usr/local/bin/g++ g++ /usr/bin/g++-10 1
hash -r

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
dnf update -y && dnf install -y sudo git python3 python3-distro gcc-toolset-11
./install_prerequisites.py
scl enable gcc-toolset-11 bash
make # or "make server" for packages specific to building the iRODS server.
```

# FAQ

### Q. Can I build an externals package using a different repository?
Yes. Open `versions.json`, find the package of interest, and set the `"git_repository"` property to the URL of the repository to clone. If this property is not present, it means the build will clone the forked repository under https://github.com/irods. The build expects that the clone will have a directory name matching the name of the forked project under https://github.com/irods.

Defining a different git repository to use for an external normally means a change in the version. For that reason, it is important to remember that `"commitish"` is required to match a **branch name** or **tag**. If you want to use a **SHA** for the `"commitish"`, you'll need to set `"enable_sha"` to `true`. This instructs the build system to separate the fetching/checking-out of a commit from the cloning of the repository. To better explain what this means, see below.

If `"enable_sha"` is set to `false` or isn't defined for a package, the build system will do the following:
```bash
$ git clone --depth 1 --branch <branch_name_or_tag> --recurse-submodules <git_repository>
```
If `"enable_sha"` is set to `true`, the build system will do this instead:
```bash
$ git clone --recurse-submodules <git_repository>
$ cd <git_repository>
$ git fetch
$ git checkout <sha> # Or branch name, or tag.
```
