import unittest
from importlib.metadata import version
from pathlib import Path
from threading import Thread
from unittest import TestCase

import requests
from common_utility import delete_directory, render_template_file, ReusableTimer
from context_logger import setup_logging
from gnupg import GPG
from test_utility import wait_for_condition, compare_lines
from watchdog.observers import Observer

from apt_repository import ReleaseSigner, LinkedPoolAptRepository, PublicGpgKey, PrivateGpgKey
from apt_server import AptServer, DirectoryService, WebServer, ServerConfig, DirectoryConfig, AptServerConfig
from tests import create_test_packages, TEST_RESOURCE_ROOT, RESOURCE_ROOT, REPOSITORY_DIR

APPLICATION_NAME = 'apt-server'
ARCHITECTURE = 'amd64'
DISTRIBUTION = 'stable'
PACKAGE_DIR = Path(f'{TEST_RESOURCE_ROOT}/test-debs')
RELEASE_TEMPLATE_PATH = Path(f'{RESOURCE_ROOT}/templates/Release.j2')
PRIVATE_KEY_PATH = Path(f'{TEST_RESOURCE_ROOT}/keys/private-key.asc')
PUBLIC_KEY_PATH = Path(f'{TEST_RESOURCE_ROOT}/keys/public-key.asc')
PUBLIC_KEY_NAME = 'test.gpg.key'
KEY_ID = 'C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3'
PASSPHRASE = 'test1234'
SERVER_HOST = 'http://127.0.0.1'
SERVER_PORT = 9000
DIRECTORY_TEMPLATE_PATH = Path(f'{RESOURCE_ROOT}/templates/directory.j2')


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
        timer, apt_repository, apt_signer, web_server, directory_service, config = create_components()

        with AptServer(timer, apt_repository, apt_signer, Observer(), directory_service, config) as apt_server:
            Thread(target=apt_server.run).start()
            wait_for_condition(3, lambda: web_server.is_running())

            # When
            response = requests.get(f'{SERVER_HOST}:{SERVER_PORT}/dists/stable/Release')

            # Then
            self.assertEqual(200, response.status_code)
            expected_lines = render_template_file(
                RELEASE_TEMPLATE_PATH,
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
            exclusions = ['', 'Date', 'Packages']
            all_matches = compare_lines(expected_lines, actual_lines, exclusions)

            self.assertTrue(all_matches)

        wait_for_condition(1, lambda: not web_server.is_running())

    def test_http_server_verification_key_mapping(self):
        # Given
        timer, apt_repository, apt_signer, web_server, directory_service, config = create_components()

        with AptServer(timer, apt_repository, apt_signer, Observer(), directory_service, config) as apt_server:
            Thread(target=apt_server.run).start()
            wait_for_condition(3, lambda: web_server.is_running())

            # When
            response = requests.get(f'{SERVER_HOST}:{SERVER_PORT}/{PUBLIC_KEY_NAME}')

            # Then
            self.assertEqual(200, response.status_code)
            with open(PUBLIC_KEY_PATH, 'r') as expected_file:
                expected_content = expected_file.read()
                actual_content = response.content.decode(response.apparent_encoding)

                self.assertEqual(expected_content, actual_content)

        wait_for_condition(1, lambda: not web_server.is_running())

    def test_http_server_package_file_mapping(self):
        # Given
        timer, apt_repository, apt_signer, web_server, directory_service, config = create_components()

        with AptServer(timer, apt_repository, apt_signer, Observer(), directory_service, config) as apt_server:
            Thread(target=apt_server.run).start()
            wait_for_condition(3, lambda: web_server.is_running())

            response = requests.get(f'{SERVER_HOST}:{SERVER_PORT}/dists/stable/main/binary-amd64/Packages')
            self.assertEqual(200, response.status_code)
            packages_lines = response.content.decode(response.apparent_encoding).splitlines()
            package_path = filter(lambda x: x.startswith('Filename:'), packages_lines).__next__().split(' ')[1]

            # When
            response = requests.get(f'{SERVER_HOST}:{SERVER_PORT}/{package_path}')

            # Then
            self.assertEqual(200, response.status_code)
            with open(f'{PACKAGE_DIR}/stable/hello-world_0.0.1-1_amd64.deb', 'rb') as expected_file:
                expected_content = expected_file.read()
                actual_content = response.content

                self.assertEqual(expected_content, actual_content)

        wait_for_condition(1, lambda: not web_server.is_running())


def create_components():
    timer = ReusableTimer()
    apt_repository = LinkedPoolAptRepository(
        APPLICATION_NAME, {ARCHITECTURE}, {DISTRIBUTION}, REPOSITORY_DIR, PACKAGE_DIR, RELEASE_TEMPLATE_PATH
    )
    gpg = GPG()
    public_key = PublicGpgKey(KEY_ID, PUBLIC_KEY_PATH, PUBLIC_KEY_NAME)
    private_key = PrivateGpgKey(KEY_ID, PRIVATE_KEY_PATH, PASSPHRASE)
    apt_signer = ReleaseSigner(gpg, public_key, private_key, REPOSITORY_DIR, {DISTRIBUTION})
    server_config = ServerConfig([f'*:{SERVER_PORT}'], 'http', '')
    web_server = WebServer(server_config)
    directory_config = DirectoryConfig(REPOSITORY_DIR, 'admin', 'admin', [], DIRECTORY_TEMPLATE_PATH)
    directory_service = DirectoryService(web_server, directory_config)
    config = AptServerConfig(PACKAGE_DIR, 0)
    return timer, apt_repository, apt_signer, web_server, directory_service, config


if __name__ == "__main__":
    unittest.main()
