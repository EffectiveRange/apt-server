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
usage: debian-package-repository.py [-h] [-c CONFIG_FILE] [-f LOG_FILE] [-l LOG_LEVEL] [--server-host SERVER_HOST] [--server-port SERVER_PORT] [--server-scheme SERVER_SCHEME] [--server-prefix SERVER_PREFIX] [--server-threads SERVER_THREADS] [--server-backlog SERVER_BACKLOG]
                                    [--server-connection-limit SERVER_CONNECTION_LIMIT] [--server-channel-timeout SERVER_CHANNEL_TIMEOUT] [--distributions DISTRIBUTIONS] [--components COMPONENTS] [--architectures ARCHITECTURES] [--repository-dir REPOSITORY_DIR] [--deb-package-dir DEB_PACKAGE_DIR]
                                    [--repo-create-delay REPO_CREATE_DELAY] [--release-template RELEASE_TEMPLATE] [--private-key-id PRIVATE_KEY_ID] [--private-key-path PRIVATE_KEY_PATH] [--private-key-pass PRIVATE_KEY_PASS] [--public-key-path PUBLIC_KEY_PATH] [--public-key-name PUBLIC_KEY_NAME]
                                    [--directory-username DIRECTORY_USERNAME] [--directory-password DIRECTORY_PASSWORD] [--directory-template DIRECTORY_TEMPLATE] [--directory-private [DIRECTORY_PRIVATE ...]]

options:
  -h, --help            show this help message and exit
  -c CONFIG_FILE, --config-file CONFIG_FILE
                        configuration file (default: /etc/effective-range/debian-package-repository/debian-package-repository.conf)
  -f LOG_FILE, --log-file LOG_FILE
                        log file path (default: None)
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        logging level (default: None)
  --server-host SERVER_HOST
                        server host to listen on (default: None)
  --server-port SERVER_PORT
                        server port to listen on (default: None)
  --server-scheme SERVER_SCHEME
                        server URL scheme (default: None)
  --server-prefix SERVER_PREFIX
                        server URL prefix (default: None)
  --server-threads SERVER_THREADS
                        server threads (default: None)
  --server-backlog SERVER_BACKLOG
                        server backlog (default: None)
  --server-connection-limit SERVER_CONNECTION_LIMIT
                        server connection limit (default: None)
  --server-channel-timeout SERVER_CHANNEL_TIMEOUT
                        server channel timeout (default: None)
  --distributions DISTRIBUTIONS
                        supported distributions (comma separated) (default: None)
  --components COMPONENTS
                        supported components (comma separated) (default: None)
  --architectures ARCHITECTURES
                        served package architectures (comma separated) (default: None)
  --repository-dir REPOSITORY_DIR
                        repository root directory (default: None)
  --deb-package-dir DEB_PACKAGE_DIR
                        directory containing the debian packages (default: None)
  --repo-create-delay REPO_CREATE_DELAY
                        repository creation delay after package changes (default: None)
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
  --public-key-name PUBLIC_KEY_NAME
                        name of the public key in the repository root (default: None)
  --directory-username DIRECTORY_USERNAME
                        username for the directory service (default: None)
  --directory-password DIRECTORY_PASSWORD
                        password for the directory service (default: None)
  --directory-template DIRECTORY_TEMPLATE
                        directory template file to use (default: None)
  --directory-private [DIRECTORY_PRIVATE ...]
                        private directory patterns (glob patterns) (default: None)
``` 

## Configuration

Default configuration (config/debian-package-repository.conf):

```ini
[logging]
log_level = info
log_file = /var/log/effective-range/debian-package-repository/debian-package-repository.log

[server]
server_host = *
server_port = 9000
server_scheme = http
server_threads = 32
server_backlog = 1024
server_connection_limit = 1000
server_channel_timeout = 60

[repository]
distributions = bookworm, trixie
components = main
architectures = amd64, arm64, armhf
repository_dir = /etc/debian-package-repository
deb_package_dir = /opt/debs
repo_create_delay = 10

[signature]
private_key_id = C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3
private_key_path = tests/keys/private-key.asc
private_key_pass = test1234
public_key_path = tests/keys/public-key.asc
public_key_name = repository.gpg.key

[directory]
directory_username = admin
directory_password = admin
```

### Example

```bash
$ bin/debian-package-repository.py
```

Output:

```bash
$ bin/debian-package-repository.py --repository-dir /tmp/aptrepo --deb-package-dir /tmp/opt/debs
2026-02-04T18:12:24.017554Z [info     ] Loading default configuration  [ConfigLoader] app_version=1.5.0 application=debian-package-repository config_file=/home/attilagombos/EffectiveRange2/debian-package-repository/config/debian-package-repository.conf hostname=Legion7iPro
2026-02-04T18:12:24.018284Z [info     ] Loading custom configuration   [ConfigLoader] app_version=1.5.0 application=debian-package-repository config_file=/etc/effective-range/debian-package-repository/debian-package-repository.conf hostname=Legion7iPro
2026-02-04T18:12:24.018615Z [info     ] Loading command line arguments [ConfigLoader] app_version=1.5.0 application=debian-package-repository arguments={'config_file': '/etc/effective-range/debian-package-repository/debian-package-repository.conf', 'repository_dir': '/tmp/aptrepo', 'deb_package_dir': '/tmp/opt/debs'} hostname=Legion7iPro
2026-02-04T18:12:24.018817Z [info     ] Configuration loaded           [ConfigLoader] app_version=1.5.0 application=debian-package-repository configuration={'log_level': 'info', 'log_file': '/var/log/effective-range/debian-package-repository/debian-package-repository.log', 'server_host': '*', 'server_port': '9000', 'distributions': 'bookworm, trixie', 'components': 'main', 'architectures': 'amd64, arm64, armhf', 'repository_dir': '/tmp/aptrepo', 'deb_package_dir': '/tmp/opt/debs', 'repo_create_delay': '10', 'private_key_id': 'C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3', 'private_key_path': 'tests/keys/private-key.asc', 'private_key_pass': 'test1234', 'public_key_path': 'tests/keys/public-key.asc', 'public_key_name': 'repository.gpg.key', 'directory_username': 'admin', 'directory_password': 'admin', 'config_file': '/etc/effective-range/debian-package-repository/debian-package-repository.conf'} hostname=Legion7iPro
2026-02-04T18:12:24.019092Z [info     ] Started debian-package-repository [PackageRepositoryApp] app_version=1.5.0 application=debian-package-repository hostname=Legion7iPro
2026-02-04T18:12:24.044297Z [info     ] Starting service               [RepositoryServer] app_version=1.5.0 application=debian-package-repository hostname=Legion7iPro service=repository-service
2026-02-04T18:12:24.045369Z [info     ] Initializing repository        [RepositoryService] app_version=1.5.0 application=debian-package-repository hostname=Legion7iPro
2026-02-04T18:12:24.046124Z [info     ] Linking package pool directory [RepositoryCreator] app_version=1.5.0 application=debian-package-repository hostname=Legion7iPro source=/tmp/opt/debs target=/tmp/aptrepo/pool
2026-02-04T18:12:24.050737Z [info     ] Added public key file          [RepositorySigner] app_version=1.5.0 application=debian-package-repository file=/tmp/aptrepo/repository.gpg.key hostname=Legion7iPro
2026-02-04T18:12:24.051392Z [info     ] Updating repository            [RepositoryService] app_version=1.5.0 application=debian-package-repository distribution=trixie hostname=Legion7iPro
2026-02-04T18:12:24.201970Z [info     ] Generated Packages file        [RepositoryCreator] app_version=1.5.0 application=debian-package-repository architecture=all component=main distribution=trixie file=/tmp/aptrepo/dists/trixie/main/binary-all/Packages hostname=Legion7iPro
2026-02-04T18:12:24.790923Z [info     ] Generated Packages file        [RepositoryCreator] app_version=1.5.0 application=debian-package-repository architecture=amd64 component=main distribution=trixie file=/tmp/aptrepo/dists/trixie/main/binary-amd64/Packages hostname=Legion7iPro
2026-02-04T18:12:25.056372Z [info     ] Generated Packages file        [RepositoryCreator] app_version=1.5.0 application=debian-package-repository architecture=arm64 component=main distribution=trixie file=/tmp/aptrepo/dists/trixie/main/binary-arm64/Packages hostname=Legion7iPro
2026-02-04T18:12:25.568331Z [info     ] Generated Packages file        [RepositoryCreator] app_version=1.5.0 application=debian-package-repository architecture=armhf component=main distribution=trixie file=/tmp/aptrepo/dists/trixie/main/binary-armhf/Packages hostname=Legion7iPro
2026-02-04T18:12:25.571400Z [info     ] Generated Release file         [RepositoryCreator] app_version=1.5.0 application=debian-package-repository distribution=trixie file=/tmp/aptrepo/dists/trixie/Release hostname=Legion7iPro
2026-02-04T18:12:25.980568Z [info     ] Created signed Release file    [RepositorySigner] app_version=1.5.0 application=debian-package-repository file=/tmp/aptrepo/dists/trixie/InRelease hostname=Legion7iPro
2026-02-04T18:12:26.395102Z [info     ] Created signature file         [RepositorySigner] app_version=1.5.0 application=debian-package-repository file=/tmp/aptrepo/dists/trixie/Release.gpg hostname=Legion7iPro
2026-02-04T18:12:26.395588Z [info     ] Switching cache for distribution [RepositoryCache] app_version=1.5.0 application=debian-package-repository distribution=trixie hostname=Legion7iPro
2026-02-04T18:12:26.395872Z [info     ] Updating repository            [RepositoryService] app_version=1.5.0 application=debian-package-repository distribution=bookworm hostname=Legion7iPro
2026-02-04T18:12:26.503679Z [info     ] Generated Packages file        [RepositoryCreator] app_version=1.5.0 application=debian-package-repository architecture=all component=main distribution=bookworm file=/tmp/aptrepo/dists/bookworm/main/binary-all/Packages hostname=Legion7iPro
2026-02-04T18:12:27.093883Z [info     ] Generated Packages file        [RepositoryCreator] app_version=1.5.0 application=debian-package-repository architecture=amd64 component=main distribution=bookworm file=/tmp/aptrepo/dists/bookworm/main/binary-amd64/Packages hostname=Legion7iPro
2026-02-04T18:12:27.395114Z [info     ] Generated Packages file        [RepositoryCreator] app_version=1.5.0 application=debian-package-repository architecture=arm64 component=main distribution=bookworm file=/tmp/aptrepo/dists/bookworm/main/binary-arm64/Packages hostname=Legion7iPro
2026-02-04T18:12:27.975146Z [info     ] Generated Packages file        [RepositoryCreator] app_version=1.5.0 application=debian-package-repository architecture=armhf component=main distribution=bookworm file=/tmp/aptrepo/dists/bookworm/main/binary-armhf/Packages hostname=Legion7iPro
2026-02-04T18:12:27.978429Z [info     ] Generated Release file         [RepositoryCreator] app_version=1.5.0 application=debian-package-repository distribution=bookworm file=/tmp/aptrepo/dists/bookworm/Release hostname=Legion7iPro
2026-02-04T18:12:28.445694Z [info     ] Created signed Release file    [RepositorySigner] app_version=1.5.0 application=debian-package-repository file=/tmp/aptrepo/dists/bookworm/InRelease hostname=Legion7iPro
2026-02-04T18:12:28.873058Z [info     ] Created signature file         [RepositorySigner] app_version=1.5.0 application=debian-package-repository file=/tmp/aptrepo/dists/bookworm/Release.gpg hostname=Legion7iPro
2026-02-04T18:12:28.873526Z [info     ] Switching cache for distribution [RepositoryCache] app_version=1.5.0 application=debian-package-repository distribution=bookworm hostname=Legion7iPro
2026-02-04T18:12:28.873816Z [info     ] Watching package pool for changes [PackageWatcher] app_version=1.5.0 application=debian-package-repository directory=/tmp/opt/debs hostname=Legion7iPro
2026-02-04T18:12:28.875049Z [info     ] Starting service               [RepositoryServer] app_version=1.5.0 application=debian-package-repository hostname=Legion7iPro service=directory-service
2026-02-04T18:12:28.875586Z [info     ] Starting server                [DirectoryServer] app_version=1.5.0 application=debian-package-repository config=ServerConfig(listen=['*:9000'], url_scheme='http', url_prefix='', threads=32, backlog=1024, connection_limit=1000, channel_timeout=60) hostname=Legion7iPro
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
