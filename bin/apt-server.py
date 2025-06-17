#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import argparse
import os
import signal
from pathlib import Path
from typing import Any

from common_utility import ConfigLoader, ReusableTimer
from context_logger import get_logger, setup_logging
from gnupg import GPG
from watchdog.observers import Observer

from apt_repository.aptRepository import LinkedPoolAptRepository
from apt_repository.aptSigner import ReleaseSigner, GpgKey
from apt_server import AptServer, ServerConfig, WebServer, DirectoryConfig, DirectoryService, AptServerConfig

APPLICATION_NAME = 'apt-server'

log = get_logger('AptServerApp')


def main() -> None:
    resource_root = _get_resource_root()
    arguments = _get_arguments()

    setup_logging(APPLICATION_NAME)

    config = ConfigLoader(resource_root / f'config/{APPLICATION_NAME}.conf').load(arguments)

    _update_logging(config)

    log.info(f'Started {APPLICATION_NAME}')

    server_host = config.get('server_host', '*')
    server_port = int(config.get('server_port', 9000))
    server_scheme = config.get('server_scheme', 'http')
    server_prefix = config.get('server_prefix', '')

    architectures = {arch.strip() for arch in config['architectures'].split(',')}
    distributions = {dist.strip() for dist in config.get('distributions', 'stable').split(',')}
    repository_dir = _get_absolute_path(config.get('repository_dir', '/etc/apt-repo'))
    deb_package_dir = _get_absolute_path(config.get('deb_package_dir', '/opt/debs'))
    repo_create_delay = float(config.get('repo_create_delay', 10))
    release_template = _get_absolute_path(config.get('release_template', 'templates/Release.j2'))

    private_key_id = config.get('private_key_id', 'C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3')
    private_key_path = _get_absolute_path(config.get('private_key_path', 'tests/keys/private-key.asc'))
    private_key_pass = config.get('private_key_pass', 'test1234')
    public_key_path = _get_absolute_path(config.get('public_key_path', 'tests/keys/public-key.asc'))

    public_key = GpgKey(private_key_id, public_key_path)
    private_key = GpgKey(private_key_id, private_key_path, private_key_pass)
    apt_signer = ReleaseSigner(GPG(), public_key, private_key, repository_dir, distributions)
    apt_repository = LinkedPoolAptRepository(
        APPLICATION_NAME, architectures, distributions, repository_dir, deb_package_dir, release_template
    )

    server_config = ServerConfig([f'{server_host}:{server_port}'], server_scheme, server_prefix)
    web_server = WebServer(server_config)

    directory_username = config.get('directory_username', 'admin')
    directory_password = config.get('directory_password', 'admin')
    directory_template = _get_absolute_path(config.get('directory_template', 'templates/directory.j2'))
    directory_private_patterns = config.get('directory_private')

    private_dirs = []
    if directory_private_patterns:
        directory_private_patterns = directory_private_patterns.strip().split('\n')
        for pattern in directory_private_patterns:
            private_dirs.extend([path for path in repository_dir.joinpath('pool/main').glob(pattern) if path.is_dir()])

    directory_config = DirectoryConfig(repository_dir, directory_username, directory_password,
                                       private_dirs, directory_template)
    directory_service = DirectoryService(web_server, directory_config)
    timer = ReusableTimer()

    apt_server_config = AptServerConfig(deb_package_dir, repo_create_delay)
    apt_server = AptServer(timer, apt_repository, apt_signer, Observer(), directory_service, apt_server_config)

    def signal_handler(signum: int, frame: Any) -> None:
        log.info('Shutting down', signum=signum)
        apt_server.shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    apt_server.run()


def _get_arguments() -> dict[str, Any]:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument(
        '-c',
        '--config-file',
        help='configuration file',
        default=f'/etc/effective-range/{APPLICATION_NAME}/{APPLICATION_NAME}.conf',
    )

    parser.add_argument('-f', '--log-file', help='log file path')
    parser.add_argument('-l', '--log-level', help='logging level')

    parser.add_argument('--server-host', help='server host to listen on')
    parser.add_argument('--server-port', help='server port to listen on', type=int)
    parser.add_argument('--server-scheme', help='server URL scheme')
    parser.add_argument('--server-prefix', help='server URL prefix')

    parser.add_argument('--architectures', help='served package architectures (comma separated)')
    parser.add_argument('--distributions', help='supported distributions (comma separated)')
    parser.add_argument('--repository-dir', help='repository root directory')
    parser.add_argument('--deb-package-dir', help='directory containing the debian packages')
    parser.add_argument('--repo-create-delay', help='repository creation delay after package changes', type=float)
    parser.add_argument('--release-template', help='release template file to use')

    parser.add_argument('--private-key-id', help='ID of keys used for signing and verifying the signature')
    parser.add_argument('--private-key-path', help='path of key used for signing')
    parser.add_argument('--private-key-pass', help='passphrase of key used for signing')
    parser.add_argument('--public-key-path', help='path of key used for verification')

    parser.add_argument('--directory-username', help='username for the directory service')
    parser.add_argument('--directory-password', help='password for the directory service')
    parser.add_argument('--directory-template', help='directory template file to use')
    parser.add_argument('--directory-private', help='private directory patterns (glob patterns)', nargs='*')

    return {k: v for k, v in vars(parser.parse_args()).items() if v is not None}


def _get_resource_root() -> Path:
    return Path(os.path.dirname(__file__)).parent.absolute()


def _get_absolute_path(path: str) -> Path:
    if path.startswith('/'):
        return Path(path)
    else:
        return _get_resource_root() / path


def _update_logging(configuration: dict[str, Any]) -> None:
    log_level = configuration.get('log_level', 'INFO')
    log_file = configuration.get('log_file')
    setup_logging(APPLICATION_NAME, log_level, log_file, warn_on_overwrite=False)


if __name__ == '__main__':
    main()
