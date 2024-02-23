# External dependencies for the building and installation of iRODS

Currently tested on:

- Ubuntu 20.04
- Ubuntu 22.04
- CentOS 7
- AlmaLinux 8
- Rocky Linux 8
- Rocky Linux 9
- Debian 11
- Debian 12

# Assumptions

This repository is expected to build in a VM or container environment that is isolated from other software or build environments. Pre-written dockerfiles can be found in the [development environment repository](https://github.com/irods/irods_development_environment/).

The automated scripts run commands as `sudo` and update system libraries and compilers, etc.

In a new container, run the following:

## Ubuntu 20.04

```bash
apt-get update
apt-get install -y sudo git python3 python3-distro
./install_prerequisites.py

update-alternatives --install /usr/local/bin/gcc gcc /usr/bin/gcc-10 1
update-alternatives --install /usr/local/bin/g++ g++ /usr/bin/g++-10 1
hash -r

make # or "make server" for packages specific to building the iRODS server.
```

## Ubuntu 22.04, Debian 11, and Debian 12

```bash
apt-get update
apt-get install -y sudo git python3 python3-distro
./install_prerequisites.py

make # or "make server" for packages specific to building the iRODS server.
```

## RHEL / CentOS 7

```bash
yum install -y sudo git python3 centos-release-scl epel-release
yum install -y python36-distro devtoolset-10-gcc devtoolset-10-gcc-c++

# Installing the prerequistes must be done before enabling the GCC compiler
# environment.
./install_prerequisites.py

# Enable the GCC 10 compiler tools.
scl enable devtoolset-10 bash

make # or "make server" for packages specific to building the iRODS server.
```

## RHEL / AlmaLinux / Rocky Linux 8

```bash
dnf config-manager --set-enabled powertools
dnf install -y sudo git python3 python3-distro gcc-toolset-11

# Installing the prerequistes must be done before enabling the GCC compiler
# environment.
./install_prerequisites.py

# Enable the GCC 11 compiler tools.
scl enable gcc-toolset-11 bash

make # or "make server" for packages specific to building the iRODS server.
```

## RHEL / AlmaLinux / Rocky Linux 9

```bash
dnf config-manager --set-enabled crb
dnf install -y sudo git python3 python3-distro
./install_prerequisites.py
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

### Q. What are `consortium_build_number` and `package_revision` in `versions.json`?
These fields allow for changes to the packaging and build process of a package without having to change the version of the software being packaged. `consortium_build_number` affects the package *name* and `package_revision` affects the package *version*.

Here's a quick guide on when these fields should be incremented or reset:  
- When bumping `consortium_build_number`, `package_revision` should be reset to `0`.
- When bumping the version of the software being packaged, both `consortium_build_number` and `package_revision` should be reset to `0`, and `consortium_build_number` of any dependant packages should be incremented, unless they are also being updated.
- When making a change to the packaging or build process of a package without changing the version of the software being packaged, consider whether the updated package should *replace* the previous version, or if it should be installable *alongside* the previous version of the package.
    - If the updated package should replace the previous version of the package, increment `package_revision`. If any dependant packages are affected by the change, increment their `package_revision` as well.
    - If the updated package should be installable alongside the previous version of the package, increment `consortium_build_number`. The `consortium_build_number` of any dependant packages will need to be incremented as well.
