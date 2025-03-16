import unittest
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer, HTTPServer
from importlib.metadata import version
from threading import Thread
from unittest import TestCase

import requests
from common_utility import delete_directory
from context_logger import setup_logging
from gnupg import GPG
from test_utility import wait_for_condition
from watchdog.observers import Observer

from apt_repository import ReleaseSigner, LinkedPoolAptRepository, GpgKey
from apt_server import AptServer
from tests import create_test_packages, compare_lines, fill_template, TEST_RESOURCE_ROOT, RESOURCE_ROOT, REPOSITORY_DIR

APPLICATION_NAME = 'apt-server'
ARCHITECTURE = 'amd64'
DISTRIBUTION = 'stable'
PACKAGE_DIR = f'{TEST_RESOURCE_ROOT}/test-debs'
TEMPLATE_PATH = f'{RESOURCE_ROOT}/templates/Release.template'
PRIVATE_KEY_PATH = f'{TEST_RESOURCE_ROOT}/keys/private-key.asc'
PUBLIC_KEY_PATH = f'{TEST_RESOURCE_ROOT}/keys/public-key.asc'
KEY_ID = 'C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3'
PASSPHRASE = 'test1234'
SERVER_HOST = 'http://127.0.0.1'


class AptServerIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging(APPLICATION_NAME, 'DEBUG', warn_on_overwrite=False)
        delete_directory(PACKAGE_DIR)
        create_test_packages(PACKAGE_DIR, DISTRIBUTION)

    def setUp(self):
        print()

    def test_http_server_repository_tree_mapping(self):
        # Given
        apt_repository, apt_signer, web_server = create_components()

        with AptServer(apt_repository, apt_signer, Observer(), web_server, PACKAGE_DIR) as apt_server:
            Thread(target=apt_server.run).start()
            wait_for_initialization_completed(web_server)

            # When
            response = requests.get(f'{SERVER_HOST}:{web_server.server_port}/dists/stable/Release')

            # Then
            self.assertEqual(200, response.status_code)
            expected_lines = fill_template(
                TEMPLATE_PATH,
                {
                    'origin': APPLICATION_NAME,
                    'label': APPLICATION_NAME,
                    'codename': DISTRIBUTION,
                    'version': version(APPLICATION_NAME),
                    'architectures': 'all amd64',
                },
            ).splitlines(True)
            expected_lines.append(f'SignWith: {KEY_ID}')
            actual_lines = response.content.decode(response.apparent_encoding).splitlines(True)
            exclusions = ['{{', 'Date', 'Packages']
            all_matches = compare_lines(expected_lines, actual_lines, exclusions)

            self.assertTrue(all_matches)

    def test_http_server_verification_key_mapping(self):
        # Given
        apt_repository, apt_signer, web_server = create_components()

        with AptServer(apt_repository, apt_signer, Observer(), web_server, PACKAGE_DIR) as apt_server:
            Thread(target=apt_server.run).start()
            wait_for_initialization_completed(web_server)

            # When
            response = requests.get(f'{SERVER_HOST}:{web_server.server_port}/dists/stable/public.key')

            # Then
            self.assertEqual(200, response.status_code)
            with open(PUBLIC_KEY_PATH, 'r') as expected_file:
                expected_content = expected_file.read()
                actual_content = response.content.decode(response.apparent_encoding)

                self.assertEqual(expected_content, actual_content)

    def test_http_server_package_file_mapping(self):
        # Given
        apt_repository, apt_signer, web_server = create_components()

        with AptServer(apt_repository, apt_signer, Observer(), web_server, PACKAGE_DIR) as apt_server:
            Thread(target=apt_server.run).start()
            wait_for_initialization_completed(web_server)

            response = requests.get(f'{SERVER_HOST}:{web_server.server_port}/dists/stable/main/binary-amd64/Packages')
            self.assertEqual(200, response.status_code)
            packages_lines = response.content.decode(response.apparent_encoding).splitlines()
            package_path = filter(lambda x: x.startswith('Filename:'), packages_lines).__next__().split(' ')[1]

            # When
            response = requests.get(f'{SERVER_HOST}:{web_server.server_port}/{package_path}')

            # Then
            self.assertEqual(200, response.status_code)
            with open(f'{PACKAGE_DIR}/stable/hello-world_0.0.1-1_amd64.deb', 'rb') as expected_file:
                expected_content = expected_file.read()
                actual_content = response.content

                self.assertEqual(expected_content, actual_content)


def create_components():
    gpg = GPG()
    public_key = GpgKey(KEY_ID, PUBLIC_KEY_PATH)
    private_key = GpgKey(KEY_ID, PRIVATE_KEY_PATH, PASSPHRASE)
    apt_signer = ReleaseSigner(gpg, public_key, private_key, REPOSITORY_DIR, {DISTRIBUTION})
    apt_repository = LinkedPoolAptRepository(
        APPLICATION_NAME, {ARCHITECTURE}, {DISTRIBUTION}, REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH
    )
    handler_class = partial(SimpleHTTPRequestHandler, directory=REPOSITORY_DIR)
    web_server = ThreadingHTTPServer(('', 0), handler_class)

    return apt_repository, apt_signer, web_server


def wait_for_initialization_completed(web_server: HTTPServer):
    wait_for_condition(5, lambda server: not server._BaseServer__is_shut_down.is_set(), web_server)


if __name__ == "__main__":
    unittest.main()
