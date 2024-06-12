# apt-server

APT server with dynamic package pool handling. Dynamic behavior is achieved by listening file changes in package pool
directory and
on any .deb file change, the repository is updated and re-signed.

## Table of contents

- [Features](#features)
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

- Dynamic package pool handling
- Multiple architectures
- GPG signed repository

## Requirements

- [Python3](https://www.python.org/downloads/)
- [GnuPG](https://gnupg.org/download/)

## Installation

### From source

Clone the repository and install the package with apt.

```commandline
make package
apt install apt-server_1.0.0_all.deb
```

### From GitHub release

Download the latest release from the GitHub repository and install the package with apt.

```commandline
apt install apt-server_1.0.0_all.deb
``` 

## Usage

```commandline
$ bin/apt-server.py --help
usage: apt-server.py [-h] [--log-file LOG_FILE] [--log-level LOG_LEVEL] [-a ARCHITECTURES [ARCHITECTURES ...]] [-r REPOSITORY_DIR] [-d DEB_PACKAGE_DIR] [-t RELEASE_TEMPLATE] [-i SIGNING_KEY_ID] [-k SIGNING_KEY_PATH] [-p SIGNING_KEY_PASS] [-P PUBLIC_KEY_PATH] [--port PORT]

optional arguments:
  -h, --help            show this help message and exit
  --log-file LOG_FILE   log file path (default: /var/log/effective-range/apt-server/apt-server.log)
  --log-level LOG_LEVEL
                        logging level (default: None)
  -a ARCHITECTURES [ARCHITECTURES ...], --architectures ARCHITECTURES [ARCHITECTURES ...]
                        list of package architectures (default: ['amd64'])
  -r REPOSITORY_DIR, --repository-dir REPOSITORY_DIR
                        repository root directory (default: /etc/apt-repo)
  -d DEB_PACKAGE_DIR, --deb-package-dir DEB_PACKAGE_DIR
                        directory containing the debian packages (default: /opt/debs)
  -t RELEASE_TEMPLATE, --release-template RELEASE_TEMPLATE
                        release template file to use (default: templates/Release.template)
  -i SIGNING_KEY_ID, --signing-key-id SIGNING_KEY_ID
                        ID of key used for signing (default: C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3)
  -k SIGNING_KEY_PATH, --signing-key-path SIGNING_KEY_PATH
                        path of key used for signing (default: tests/keys/private-key.asc)
  -p SIGNING_KEY_PASS, --signing-key-pass SIGNING_KEY_PASS
                        passphrase of key used for signing (default: admin123)
  -P PUBLIC_KEY_PATH, --public-key-path PUBLIC_KEY_PATH
                        path of key used for verification (default: tests/keys/public-key.asc)
  --port PORT           repository server port to listen on (default: 9000)
``` 

Example:

```commandline
$ bin/apt-server.py -a armhf -t templates/Release.template -k tests/keys/private-key.asc -P tests/keys/public-key.asc
```

Output:

```commandline
2024-03-08T10:24:53.723322Z [info     ] Started apt-server             [AptServerMain] app_version=1.1.1 application=apt-server arguments={'architectures': ['armhf'], 'repository_dir': '/etc/apt-repo', 'deb_package_dir': '/opt/debs', 'release_template': '/opt/venvs/apt-server/templates/Release.template', 'signing_key_id': 'C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3', 'signing_key_path': '/opt/venvs/apt-server/.gnupg/private-key.asc', 'signing_key_pass': 'admin123', 'public_key_path': '/opt/venvs/apt-server/.gnupg/public-key.asc', 'port': 9000} hostname=er-debian
2024-03-08T10:24:53.725250Z [info     ] Creating initial repository    [AptServer] app_version=1.1.1 application=apt-server hostname=er-debian
2024-03-08T10:24:53.726090Z [info     ] Creating pool directory        [AptRepository] app_version=1.1.1 application=apt-server directory=/etc/apt-repo/pool hostname=er-debian
2024-03-08T10:24:53.726980Z [info     ] Creating .deb package directory [AptRepository] app_version=1.1.1 application=apt-server directory=/opt/debs hostname=er-debian
2024-03-08T10:24:53.727728Z [info     ] Linked .deb package directory  [AptRepository] app_version=1.1.1 application=apt-server hostname=er-debian source=/opt/debs target=/etc/apt-repo/pool/main
2024-03-08T10:24:53.761824Z [info     ] Generated Packages file        [AptRepository] app_version=1.1.1 application=apt-server architecture=all file=/etc/apt-repo/dists/stable/main/binary-all/Packages hostname=er-debian
2024-03-08T10:24:53.796222Z [info     ] Generated Packages file        [AptRepository] app_version=1.1.1 application=apt-server architecture=armhf file=/etc/apt-repo/dists/stable/main/binary-armhf/Packages hostname=er-debian
2024-03-08T10:24:53.799556Z [info     ] Generated Release file         [AptRepository] app_version=1.1.1 application=apt-server file=/etc/apt-repo/dists/stable/Release hostname=er-debian
2024-03-08T10:24:53.800474Z [info     ] Signing repository             [AptRepository] app_version=1.1.1 application=apt-server hostname=er-debian
2024-03-08T10:24:55.088156Z [info     ] Created signed Release file    [AptSigner] app_version=1.1.1 application=apt-server file=/etc/apt-repo/dists/stable/InRelease hostname=er-debian
2024-03-08T10:24:55.448641Z [info     ] Created signature file         [AptSigner] app_version=1.1.1 application=apt-server file=/etc/apt-repo/dists/stable/Release.gpg hostname=er-debian
2024-03-08T10:24:55.449915Z [info     ] Added public key file          [AptSigner] app_version=1.1.1 application=apt-server file=/etc/apt-repo/dists/stable/public.key hostname=er-debian
2024-03-08T10:24:55.450723Z [info     ] Watching directory for .deb file changes [AptServer] app_version=1.1.1 application=apt-server directory=/opt/debs hostname=er-debian
2024-03-08T10:24:55.451555Z [info     ] Starting component             [AptServer] app_version=1.1.1 application=apt-server component=file-observer hostname=er-debian
2024-03-08T10:24:55.452823Z [info     ] Starting component             [AptServer] app_version=1.1.1 application=apt-server component=web-server hostname=er-debian
...
2024-03-08T12:01:56.750346Z [info     ] Shutting down                  [AptServerMain] app_version=1.1.1 application=apt-server hostname=er-debian signum=2
```

## Accessing the repository

1. Add the repository to sources list

   The repository can be accessed by adding it to a sources list file, eg:

    ```commandline
    echo "deb [arch=armhf] http://127.0.0.1:9000 stable main" | tee /etc/apt/sources.list.d/effective-range.list
    ```

2. Add the public key to the keychain

   The public key of the private key that was used to sign the repository needs to be added to the keychain, eg:

    ```commandline
    apt-key adv --fetch-keys http://127.0.0.1:9000/dists/stable/public.key
    ```

3. Update the package list

   The package list can be updated with apt-get, eg:

    ```commandline
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

```commandline
gpg --gen-key
```

### Exporting keys

Keys can be exported to ASCII files to be portable between keychains.

```commandline
gpg --output public.pgp --armor --export username@email
```

```commandline
gpg --output private.pgp --armor --export-secret-key username@email
```

### Using exported private key

If the key pair was generated on a different system than the one the APT repository is hosted, the exported private key
should be imported to the host's keychain.

```commandline
gpg --import private.pgp
```

## Client side

### Using exported public key

Clients accessing the APT repository needs the public key of the private key that was used to sign the repository. This
public key can be used by the APT clients to verify the repository's signature and consider it secure.

```commandline
apt-key add public.pgp
```
