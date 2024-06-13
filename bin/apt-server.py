#!/usr/bin/env python3

# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import argparse
import os
import signal
from functools import partial
from http.server import SimpleHTTPRequestHandler, HTTPServer
from pathlib import Path
from typing import Any

from context_logger import get_logger, setup_logging
from gnupg import GPG
from watchdog.observers import Observer

from apt_repository.aptRepository import LinkedPoolAptRepository
from apt_repository.aptSigner import ReleaseSigner, GpgKey
from apt_server import AptServer

APPLICATION_NAME = 'apt-server'

log = get_logger('AptServerApp')


def main() -> None:
    arguments = _get_argument_parser().parse_args()

    setup_logging(APPLICATION_NAME, arguments.log_level, arguments.log_file)

    log.info('Started apt-server', arguments=vars(arguments))

    resource_root = _get_resource_root()
    repository_dir = _get_absolute_path(resource_root, arguments.repository_dir)
    deb_package_dir = _get_absolute_path(resource_root, arguments.deb_package_dir)
    private_key_path = _get_absolute_path(resource_root, arguments.private_key_path)
    public_key_path = _get_absolute_path(resource_root, arguments.public_key_path)
    release_template_path = _get_absolute_path(resource_root, arguments.release_template)

    public_key = GpgKey(arguments.key_id, public_key_path)
    private_key = GpgKey(arguments.key_id, private_key_path, arguments.private_key_pass)
    apt_signer = ReleaseSigner(GPG(), public_key, private_key, repository_dir)
    apt_repository = LinkedPoolAptRepository(APPLICATION_NAME, arguments.architectures, repository_dir,
                                             deb_package_dir, release_template_path)

    handler_class = partial(SimpleHTTPRequestHandler, directory=repository_dir)
    web_server = HTTPServer(('', arguments.port), handler_class)

    apt_server = AptServer(apt_repository, apt_signer, Observer(), web_server, deb_package_dir)

    def signal_handler(signum: int, frame: Any) -> None:
        log.info('Shutting down', signum=signum)
        apt_server.shutdown()

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    apt_server.run()


def _get_argument_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument('--log-file', help='log file path',
                        default='/var/log/effective-range/apt-server/apt-server.log')
    parser.add_argument('--log-level', help='logging level', default='info')
    parser.add_argument('-a', '--architectures', help='list of package architectures', nargs='+', default=['amd64'])
    parser.add_argument('-r', '--repository-dir', help='repository root directory', default='/etc/apt-repo')
    parser.add_argument('-d', '--deb-package-dir', help='directory containing the debian packages', default='/opt/debs')
    parser.add_argument('-t', '--release-template', help='release template file to use',
                        default='templates/Release.template')
    parser.add_argument('-i', '--key-id', help='ID of key pair used for signing and verifying the signature',
                        default='C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3')
    parser.add_argument('-k', '--private-key-path', help='path of key used for signing',
                        default='tests/keys/private-key.asc')
    parser.add_argument('-p', '--private-key-pass', help='passphrase of key used for signing',
                        default='test1234')
    parser.add_argument('-P', '--public-key-path', help='path of key used for verification',
                        default='tests/keys/public-key.asc')
    parser.add_argument('--port', help='repository server port to listen on', default=9000, type=int)
    return parser


def _get_resource_root() -> str:
    return str(Path(os.path.dirname(__file__)).parent.absolute())


def _get_absolute_path(resource_root: str, path: str) -> str:
    if path.startswith('/'):
        return path
    else:
        return f'{resource_root}/{path}'


if __name__ == '__main__':
    main()
