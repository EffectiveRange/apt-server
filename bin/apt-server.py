#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import argparse
import os
import signal
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any

from common_utility import ConfigLoader
from context_logger import get_logger, setup_logging
from gnupg import GPG
from watchdog.observers import Observer

from apt_repository.aptRepository import LinkedPoolAptRepository
from apt_repository.aptSigner import ReleaseSigner, GpgKey
from apt_server import AptServer

APPLICATION_NAME = 'apt-server'

log = get_logger('AptServerApp')


def main() -> None:
    resource_root = _get_resource_root()
    arguments = _get_arguments()

    setup_logging(APPLICATION_NAME)

    config = ConfigLoader(resource_root / f'config/{APPLICATION_NAME}.conf').load(arguments)

    _update_logging(config)

    log.info(f'Started {APPLICATION_NAME}', arguments=config)

    server_port = int(config.get('server_port', 9000))

    architectures = {arch.strip() for arch in config['architectures'].split(',')}
    distributions = {dist.strip() for dist in config.get('distributions', 'stable').split(',')}
    repository_dir = _get_absolute_path(config.get('repository_dir', '/etc/apt-repo'))
    deb_package_dir = _get_absolute_path(config.get('deb_package_dir', '/opt/debs'))
    release_template = _get_absolute_path(config.get('release_template', 'templates/Release.template'))

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

    handler_class = partial(SimpleHTTPRequestHandler, directory=str(repository_dir))
    web_server = ThreadingHTTPServer(('', server_port), handler_class)

    apt_server = AptServer(apt_repository, apt_signer, Observer(), web_server, deb_package_dir)

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

    parser.add_argument('--server-port', help='repository server port to listen on', default=9000, type=int)

    parser.add_argument('--architectures', help='served package architectures (comma separated)')
    parser.add_argument('--distributions', help='supported distributions (comma separated)')
    parser.add_argument('--repository-dir', help='repository root directory')
    parser.add_argument('--deb-package-dir', help='directory containing the debian packages')
    parser.add_argument('--release-template', help='release template file to use')

    parser.add_argument('--private-key-id', help='ID of keys used for signing and verifying the signature')
    parser.add_argument('--private-key-path', help='path of key used for signing')
    parser.add_argument('--private-key-pass', help='passphrase of key used for signing')
    parser.add_argument('--public-key-path', help='path of key used for verification')

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
