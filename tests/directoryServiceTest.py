import base64
import unittest
from pathlib import Path
from unittest import TestCase

from common_utility import delete_directory
from context_logger import setup_logging
from test_utility import wait_for_condition

from apt_server import WebServer, ServerConfig, DirectoryConfig, DirectoryService
from tests import (
    create_test_packages,
    TEST_RESOURCE_ROOT,
    RESOURCE_ROOT
)

DISTRIBUTION = 'stable'
PACKAGE_DIR = Path(f'{TEST_RESOURCE_ROOT}/test-debs')


class DirectoryServiceTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('apt-server', 'DEBUG', warn_on_overwrite=False)
        delete_directory(PACKAGE_DIR)
        create_test_packages(PACKAGE_DIR, DISTRIBUTION)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        web_server, config = create_components()

        with DirectoryService(web_server, config) as directory_service:
            # When
            directory_service.start()

            # Then
            wait_for_condition(1, lambda: web_server.is_running())

        wait_for_condition(1, lambda: not web_server.is_running())

    def test_returns_200_when_accessing_public_directory(self):
        # Given
        web_server, config = create_components()

        with DirectoryService(web_server, config) as directory_service:
            # When
            directory_service.start()

            wait_for_condition(1, lambda: web_server.is_running())

            client = web_server._app.test_client()

            # When
            response = client.get('/')

            # Then
            self.assertEqual(200, response.status_code)

    def test_returns_200_when_accessing_public_file(self):
        # Given
        web_server, config = create_components()

        with DirectoryService(web_server, config) as directory_service:
            # When
            directory_service.start()

            wait_for_condition(1, lambda: web_server.is_running())

            client = web_server._app.test_client()

            # When
            response = client.get('/stable/hello-world_0.0.1-1_amd64.deb')

            # Then
            self.assertEqual(200, response.status_code)

    def test_returns_200_when_accessing_private_directory_with_auth(self):
        # Given
        web_server, config = create_components()
        config.private_dirs = [PACKAGE_DIR / 'stable']

        with DirectoryService(web_server, config) as directory_service:
            # When
            directory_service.start()

            wait_for_condition(1, lambda: web_server.is_running())

            client = web_server._app.test_client()

            credentials = base64.b64encode(f'{config.username}:{config.password}'.encode()).decode()

            # When
            response = client.get('/stable', headers={'Authorization': f'Basic {credentials}'})

            # Then
            self.assertEqual(200, response.status_code)

    def test_returns_200_when_accessing_private_file_with_auth(self):
        # Given
        web_server, config = create_components()
        config.private_dirs = [PACKAGE_DIR / 'stable']

        with DirectoryService(web_server, config) as directory_service:
            # When
            directory_service.start()

            wait_for_condition(1, lambda: web_server.is_running())

            client = web_server._app.test_client()

            credentials = base64.b64encode(f'{config.username}:{config.password}'.encode()).decode()

            # When
            response = client.get('/stable/hello-world_0.0.1-1_amd64.deb',
                                  headers={'Authorization': f'Basic {credentials}'})

            # Then
            self.assertEqual(200, response.status_code)

    def test_returns_401_when_accessing_private_directory_without_auth(self):
        # Given
        web_server, config = create_components()
        config.private_dirs = [PACKAGE_DIR / 'stable']

        with DirectoryService(web_server, config) as directory_service:
            # When
            directory_service.start()

            wait_for_condition(1, lambda: web_server.is_running())

            client = web_server._app.test_client()

            # When
            response = client.get('/stable')

            # Then
            self.assertEqual(401, response.status_code)

    def test_returns_401_when_accessing_private_file_without_auth(self):
        # Given
        web_server, config = create_components()
        config.private_dirs = [PACKAGE_DIR / 'stable']

        with DirectoryService(web_server, config) as directory_service:
            # When
            directory_service.start()

            wait_for_condition(1, lambda: web_server.is_running())

            client = web_server._app.test_client()

            # When
            response = client.get('/stable/hello-world_0.0.1-1_amd64.deb')

            # Then
            self.assertEqual(401, response.status_code)

    def test_returns_404_when_accessing_non_existing_path(self):
        # Given
        web_server, config = create_components()

        with DirectoryService(web_server, config) as directory_service:
            # When
            directory_service.start()

            wait_for_condition(1, lambda: web_server.is_running())

            client = web_server._app.test_client()

            # When
            response = client.get('/stable/invalid')

            # Then
            self.assertEqual(404, response.status_code)


def create_components():
    web_server = WebServer(ServerConfig(['*:0']))
    config = DirectoryConfig(PACKAGE_DIR, 'admin', 'admin', [],
                             Path(f'{RESOURCE_ROOT}/templates/directory.j2'))
    return web_server, config


if __name__ == '__main__':
    unittest.main()
