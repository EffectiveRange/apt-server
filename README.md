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
usage: apt-server.py [-h] [-f LOG_FILE] [-l LOG_LEVEL] [-a ARCHITECTURES] [-r REPOSITORY_DIR] [-d DEB_PACKAGE_DIR] [-t RELEASE_TEMPLATE] [-i KEY_ID] [-k PRIVATE_KEY_PATH] [-p PRIVATE_KEY_PASS]
                     [-P PUBLIC_KEY_PATH] [--port PORT]

optional arguments:
  -h, --help            show this help message and exit
  -f LOG_FILE, --log-file LOG_FILE
                        log file path (default: /var/log/effective-range/apt-server/apt-server.log)
  -l LOG_LEVEL, --log-level LOG_LEVEL
                        logging level (default: info)
  -a ARCHITECTURES, --architectures ARCHITECTURES
                        served package architectures (comma separated) (default: amd64)
  -r REPOSITORY_DIR, --repository-dir REPOSITORY_DIR
                        repository root directory (default: /etc/apt-repo)
  -d DEB_PACKAGE_DIR, --deb-package-dir DEB_PACKAGE_DIR
                        directory containing the debian packages (default: /opt/debs)
  -t RELEASE_TEMPLATE, --release-template RELEASE_TEMPLATE
                        release template file to use (default: templates/Release.template)
  -i KEY_ID, --key-id KEY_ID
                        ID of key pair used for signing and verifying the signature (default: C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3)
  -k PRIVATE_KEY_PATH, --private-key-path PRIVATE_KEY_PATH
                        path of key used for signing (default: tests/keys/private-key.asc)
  -p PRIVATE_KEY_PASS, --private-key-pass PRIVATE_KEY_PASS
                        passphrase of key used for signing (default: test1234)
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
2024-06-14T08:53:22.566892Z [info     ] Started apt-server             [AptServerApp] app_version=1.1.3 application=apt-server arguments={'log_file': '/var/log/effective-range/apt-server/apt-server.log', 'log_level': 'info', 'architecture': ['amd64'], 'repository_dir': '/etc/apt-repo', 'deb_package_dir': '/opt/debs', 'release_template': 'templates/Release.template', 'key_id': 'C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3', 'private_key_path': 'tests/keys/private-key.asc', 'private_key_pass': 'test1234', 'public_key_path': 'tests/keys/public-key.asc', 'port': 9000} hostname=Legion7iPro
2024-06-14T08:53:22.619221Z [info     ] Creating initial repository    [AptServer] app_version=1.1.3 application=apt-server hostname=Legion7iPro
2024-06-14T08:53:22.657566Z [info     ] Removing existing link         [AptRepository] app_version=1.1.3 application=apt-server hostname=Legion7iPro target=/etc/apt-repo/pool/main
2024-06-14T08:53:22.696269Z [info     ] Linked .deb package directory  [AptRepository] app_version=1.1.3 application=apt-server hostname=Legion7iPro source=/opt/debs target=/etc/apt-repo/pool/main
2024-06-14T08:53:22.791912Z [info     ] Generated Packages file        [AptRepository] app_version=1.1.3 application=apt-server architecture=all file=/etc/apt-repo/dists/stable/main/binary-all/Packages hostname=Legion7iPro
2024-06-14T08:53:22.885608Z [info     ] Generated Packages file        [AptRepository] app_version=1.1.3 application=apt-server architecture=amd64 file=/etc/apt-repo/dists/stable/main/binary-amd64/Packages hostname=Legion7iPro
2024-06-14T08:53:22.969732Z [info     ] Generated Release file         [AptRepository] app_version=1.1.3 application=apt-server file=/etc/apt-repo/dists/stable/Release hostname=Legion7iPro
2024-06-14T08:53:23.000795Z [info     ] Signing initial repository     [AptServer] app_version=1.1.3 application=apt-server hostname=Legion7iPro
2024-06-14T08:53:23.061975Z [info     ] Added public key file          [AptSigner] app_version=1.1.3 application=apt-server file=/etc/apt-repo/dists/stable/public.key hostname=Legion7iPro
2024-06-14T08:53:23.554509Z [info     ] Created signed Release file    [AptSigner] app_version=1.1.3 application=apt-server file=/etc/apt-repo/dists/stable/InRelease hostname=Legion7iPro
2024-06-14T08:53:24.038852Z [info     ] Created signature file         [AptSigner] app_version=1.1.3 application=apt-server file=/etc/apt-repo/dists/stable/Release.gpg hostname=Legion7iPro
2024-06-14T08:53:24.081987Z [info     ] Watching directory for .deb file changes [AptServer] app_version=1.1.3 application=apt-server directory=/opt/debs hostname=Legion7iPro
2024-06-14T08:53:24.130686Z [info     ] Starting component             [AptServer] app_version=1.1.3 application=apt-server component=file-observer hostname=Legion7iPro
2024-06-14T08:53:24.173778Z [info     ] Starting component             [AptServer] app_version=1.1.3 application=apt-server component=web-server hostname=Legion7iPro
...
2024-06-14T08:54:10.480670Z [info     ] Shutting down                  [AptServerApp] app_version=1.1.3 application=apt-server hostname=Legion7iPro signum=2
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
