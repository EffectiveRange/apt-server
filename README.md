[![CI](https://github.com/EffectiveRange/debian-package-repository/actions/workflows/ci.yaml/badge.svg)](https://github.com/EffectiveRange/debian-package-repository/actions/workflows/ci.yaml)
[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/EffectiveRange/debian-package-repository/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/debian-package-repository/blob/python-coverage-comment-action-data/htmlcov/index.html)

# debian-package-repository

APT repository with dynamic package pool handling. Dynamic behavior is achieved by listening file changes in package pool
directory and on any .deb file change, the repository is updated and re-signed.

## Table of contents

- [Features](#features)
- [Requirements](#requirements)
- [Installation](#installation)
    - [From source](#from-source)
    - [From GitHub release](#from-github-release)
- [Usage](#usage)
- [Accessing the repository](#accessing-the-repository)
- [Key management](#key-management)
    - [Repository side](#repository-side)
        - [Generating keys](#generating-keys)
        - [Exporting keys](#exporting-keys)
        - [Using exported private key](#using-exported-private-key)
    - [Client side](#client-side)
        - [Using exported public key](#using-exported-public-key)

## Features

- [x] Dynamic package pool handling
- [x] Multiple architectures
- [x] Multiple distributions
- [x] GPG signed repository

## Requirements

- [Python3](https://www.python.org/downloads/)
- [GnuPG](https://gnupg.org/download/)

## Installation

### From source

Clone the repository and install the package with apt.

```bash
make package
apt install ./debian-package-repository_1.0.0_all.deb
```

### From GitHub release

Download the latest release from the GitHub repository and install the package with apt.

```bash
apt install ./debian-package-repository_1.0.0_all.deb
``` 

## Usage

### Command line reference

```bash
$ bin/debian-package-repository.py --help
usage: debian-package-repository.py [-h] [-c CONFIG_FILE] [-f LOG_FILE] [-l LOG_LEVEL] [--server-port SERVER_PORT] [--architectures ARCHITECTURES] [--distributions DISTRIBUTIONS] [--repository-dir REPOSITORY_DIR] [--deb-package-dir DEB_PACKAGE_DIR] [--release-template RELEASE_TEMPLATE]
                     [--private-key-id PRIVATE_KEY_ID] [--private-key-path PRIVATE_KEY_PATH] [--private-key-pass PRIVATE_KEY_PASS] [--public-key-path PUBLIC_KEY_PATH]

options:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        configuration file (default: /etc/effective-range/debian-package-repository/debian-package-repository.conf)
  -f LOG_FILE, --log-file LOG_FILE
                        log file path (default: None)
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        logging level (default: None)
  --server-port SERVER_PORT
                        repository server port to listen on (default: 9000)
  --architectures ARCHITECTURES
                        served package architectures (comma separated) (default: None)
  --distributions DISTRIBUTIONS
                        supported distributions (comma separated) (default: None)
  --repository-dir REPOSITORY_DIR
                        repository root directory (default: None)
  --deb-package-dir DEB_PACKAGE_DIR
                        directory containing the debian packages (default: None)
  --release-template RELEASE_TEMPLATE
                        release template file to use (default: None)
  --private-key-id PRIVATE_KEY_ID
                        ID of keys used for signing and verifying the signature (default: None)
  --private-key-path PRIVATE_KEY_PATH
                        path of key used for signing (default: None)
  --private-key-pass PRIVATE_KEY_PASS
                        passphrase of key used for signing (default: None)
  --public-key-path PUBLIC_KEY_PATH
                        path of key used for verification (default: None)
``` 

## Configuration

Default configuration (config/debian-package-repository.conf):

```ini
[logging]
log_level = info
log_file = /var/log/effective-range/debian-package-repository/debian-package-repository.log

[server]
server_port = 9000

[repository]
architectures = amd64, arm64, armhf
distributions = bullseye, bookworm
repository_dir = /etc/effective-range/debian-package-repository
deb_package_dir = /opt/debs
release_template = templates/Release.j2

[signature]
private_key_id = C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3
private_key_path = tests/keys/private-key.asc
private_key_pass = test1234
public_key_path = tests/keys/public-key.asc
```

### Example

```bash
$ bin/debian-package-repository.py
```

Output:

```bash
2025-03-15T16:56:23.740797Z [info     ] Using configuration file       [ConfigLoader] app_version=1.1.5 application=debian-package-repository config_file=/etc/effective-range/debian-package-repository/debian-package-repository.conf hostname=Legion7iPro
2025-03-15T16:56:23.742358Z [info     ] Started debian-package-repository             [AptServerApp] app_version=1.1.5 application=debian-package-repository arguments={'log_level': 'info', 'log_file': '/var/log/effective-range/debian-package-repository/debian-package-repository.log', 'server_port': 9000, 'architectures': 'amd64, arm64, armhf', 'distributions': 'bullseye, bookworm', 'repository_dir': '/etc/apt-repo', 'deb_package_dir': '/tmp/packages', 'release_template': 'templates/Release.j2', 'private_key_id': 'C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3', 'private_key_path': 'tests/keys/private-key.asc', 'private_key_pass': 'test1234', 'public_key_path': 'tests/keys/public-key.asc', 'config_file': '/etc/effective-range/debian-package-repository/debian-package-repository.conf'} hostname=Legion7iPro
2025-03-15T16:56:23.746562Z [info     ] Creating initial repository    [AptServer] app_version=1.1.5 application=debian-package-repository hostname=Legion7iPro
2025-03-15T16:56:23.747002Z [info     ] Removing existing link         [AptRepository] app_version=1.1.5 application=debian-package-repository hostname=Legion7iPro target=/etc/apt-repo/pool/main
2025-03-15T16:56:23.747415Z [info     ] Linked .deb package directory  [AptRepository] app_version=1.1.5 application=debian-package-repository hostname=Legion7iPro source=/tmp/packages target=/etc/apt-repo/pool/main
dpkg-scanpackages: info: Wrote 10 entries to output Packages file.
2025-03-15T16:56:23.868021Z [info     ] Generated Packages file        [AptRepository] app_version=1.1.5 application=debian-package-repository architecture=all distribution=bullseye file=/etc/apt-repo/dists/bullseye/main/binary-all/Packages hostname=Legion7iPro
dpkg-scanpackages: info: Wrote 11 entries to output Packages file.
2025-03-15T16:56:24.006407Z [info     ] Generated Packages file        [AptRepository] app_version=1.1.5 application=debian-package-repository architecture=amd64 distribution=bullseye file=/etc/apt-repo/dists/bullseye/main/binary-amd64/Packages hostname=Legion7iPro
dpkg-scanpackages: info: Wrote 11 entries to output Packages file.
2025-03-15T16:56:24.136043Z [info     ] Generated Packages file        [AptRepository] app_version=1.1.5 application=debian-package-repository architecture=arm64 distribution=bullseye file=/etc/apt-repo/dists/bullseye/main/binary-arm64/Packages hostname=Legion7iPro
dpkg-scanpackages: info: Wrote 14 entries to output Packages file.
2025-03-15T16:56:24.270599Z [info     ] Generated Packages file        [AptRepository] app_version=1.1.5 application=debian-package-repository architecture=armhf distribution=bullseye file=/etc/apt-repo/dists/bullseye/main/binary-armhf/Packages hostname=Legion7iPro
2025-03-15T16:56:24.273913Z [info     ] Generated Release file         [AptRepository] app_version=1.1.5 application=debian-package-repository distribution=bullseye file=/etc/apt-repo/dists/bullseye/Release hostname=Legion7iPro
2025-03-15T16:56:24.275394Z [info     ] Generated Release file         [AptRepository] app_version=1.1.5 application=debian-package-repository distribution=bookworm file=/etc/apt-repo/dists/bookworm/Release hostname=Legion7iPro
2025-03-15T16:56:24.275822Z [info     ] Signing initial repository     [AptServer] app_version=1.1.5 application=debian-package-repository hostname=Legion7iPro
2025-03-15T16:56:24.276210Z [info     ] Added public key file          [AptSigner] app_version=1.1.5 application=debian-package-repository file=/etc/apt-repo/dists/bullseye/public.key hostname=Legion7iPro
2025-03-15T16:56:24.692295Z [info     ] Created signed Release file    [AptSigner] app_version=1.1.5 application=debian-package-repository file=/etc/apt-repo/dists/bullseye/InRelease hostname=Legion7iPro
2025-03-15T16:56:25.096357Z [info     ] Created signature file         [AptSigner] app_version=1.1.5 application=debian-package-repository file=/etc/apt-repo/dists/bullseye/Release.gpg hostname=Legion7iPro
2025-03-15T16:56:25.504482Z [info     ] Created signed Release file    [AptSigner] app_version=1.1.5 application=debian-package-repository file=/etc/apt-repo/dists/bookworm/InRelease hostname=Legion7iPro
2025-03-15T16:56:25.913410Z [info     ] Created signature file         [AptSigner] app_version=1.1.5 application=debian-package-repository file=/etc/apt-repo/dists/bookworm/Release.gpg hostname=Legion7iPro
2025-03-15T16:56:25.914277Z [info     ] Watching directory for .deb file changes [AptServer] app_version=1.1.5 application=debian-package-repository directory=/tmp/packages hostname=Legion7iPro
2025-03-15T16:56:25.915716Z [info     ] Starting component             [AptServer] app_version=1.1.5 application=debian-package-repository component=file-observer hostname=Legion7iPro
2025-03-15T16:56:25.917301Z [info     ] Starting component             [AptServer] app_version=1.1.5 application=debian-package-repository component=web-server hostname=Legion7iPro
```

## Accessing the repository

1. Add the repository to sources list

   The repository can be accessed by adding it to a sources list file, eg:

    ```bash
    echo "deb http://127.0.0.1:9000 bullseye main" | tee /etc/apt/sources.list.d/effective-range.list
    ```

2. Add the public key to the keychain

   The public key of the private key that was used to sign the repository needs to be added to the keychain, eg:

    ```bash
    apt-key adv --fetch-keys http://127.0.0.1:9000/dists/bullseye/public.key
    ```

3. Update the package list

   The package list can be updated with apt-get, eg:

    ```bash
    apt-get update
    ```

# Key management

GPG keys are used to sign and verify the APT repositories.
The private key is used for signing and the public one is used for verifying.

## Repository side

The private key needs to be present in the host keychain. New keys can be generated or the ones under 'tests/keys' can
be used for testing.

### Generating keys

Generate keys with GnuPG interactively. It will prompt for name, e-mail and a passphrase. The generated key pair
will be added to the host's keychain and can be accessed by the passphrase.

```bash
gpg --gen-key
```

### Exporting keys

Keys can be exported to ASCII files to be portable between keychains.

```bash
gpg --output public.pgp --armor --export username@email
```

```bash
gpg --output private.pgp --armor --export-secret-key username@email
```

### Using exported private key

If the key pair was generated on a different system than the one the APT repository is hosted, the exported private key
should be imported to the host's keychain.

```bash
gpg --import private.pgp
```

## Client side

### Using exported public key

Clients accessing the APT repository needs the public key of the private key that was used to sign the repository. This
public key can be used by the APT clients to verify the repository's signature and consider it secure.

```bash
apt-key add public.pgp
```
