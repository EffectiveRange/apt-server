import unittest
from pathlib import Path
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging
from flask import Response
from test_utility import wait_for_condition
from watchdog.events import FileClosedEvent
from watchdog.observers.api import BaseObserver

from apt_server import WebServer, ServerConfig
from tests import TEST_RESOURCE_ROOT


class ApiServerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('er-scarecrow-server', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        observer, config = create_components()

        with WebServer(observer, config) as web_server:
            # When
            web_server.start()

            # Then
            wait_for_condition(1, lambda: web_server._server is not None)

        wait_for_condition(1, lambda: web_server._server is None)

    def test_returns_200(self):
        # Given
        observer, config = create_components()

        with WebServer(observer, config) as web_server:
            # When
            @web_server.get_app().route('/test', methods=['GET'])
            def get_test() -> Response:
                return Response(status=200, response='Test OK')

            web_server.start()

            wait_for_condition(1, lambda: web_server._server is not None)

            client = web_server._app.test_client()

            # When
            response = client.get('/test')

            # Then
            self.assertEqual(200, response.status_code)
            self.assertEqual('Test OK', response.data.decode())

    def test_returns_200_when_single_socket(self):
        # Given
        observer, config = create_components()
        config.listen = ['127.0.0.1:0']

        with WebServer(observer, config) as web_server:
            # When
            @web_server.get_app().route('/test', methods=['GET'])
            def get_test() -> Response:
                return Response(status=200, response='Test OK')

            web_server.start()

            wait_for_condition(1, lambda: web_server._server is not None)

            client = web_server._app.test_client()

            # When
            response = client.get('/test')

            # Then
            self.assertEqual(200, response.status_code)
            self.assertEqual('Test OK', response.data.decode())

    def test_returns_200_when_no_ssl(self):
        # Given
        observer, config = create_components()
        config = ServerConfig(['*:0'])

        with WebServer(observer, config) as web_server:
            # When
            @web_server.get_app().route('/test', methods=['GET'])
            def get_test() -> Response:
                return Response(status=200, response='Test OK')

            web_server.start()

            wait_for_condition(1, lambda: web_server._server is not None)

            client = web_server._app.test_client()

            # When
            response = client.get('/test')

            # Then
            self.assertEqual(200, response.status_code)
            self.assertEqual('Test OK', response.data.decode())

    def test_returns_200_when_cert_file_not_exists(self):
        # Given
        observer, config = create_components()
        config = ServerConfig(['*:0'], Path('/invalid.crt'), Path(f'{TEST_RESOURCE_ROOT}/keys/localhost.key'))

        with WebServer(observer, config) as web_server:
            # When
            @web_server.get_app().route('/test', methods=['GET'])
            def get_test() -> Response:
                return Response(status=200, response='Test OK')

            web_server.start()

            wait_for_condition(1, lambda: web_server._server is not None)

            client = web_server._app.test_client()

            # When
            response = client.get('/test')

            # Then
            self.assertEqual(200, response.status_code)
            self.assertEqual('Test OK', response.data.decode())

    def test_restarts_server_when_certificate_changes(self):
        # Given
        observer, config = create_components()

        with WebServer(observer, config) as web_server:
            # When
            @web_server.get_app().route('/test', methods=['GET'])
            def get_test() -> Response:
                return Response(status=200, response='Test OK')

            web_server.start()

            wait_for_condition(1, lambda: web_server._server is not None)

            server = web_server._server

            client = web_server._app.test_client()

            # When
            web_server.on_closed(FileClosedEvent(src_path=f'{TEST_RESOURCE_ROOT}/keys/localhost.crt'))

            wait_for_condition(1, lambda: web_server._server is not None and web_server._server != server)

            response = client.get('/test')

            # Then
            self.assertEqual(200, response.status_code)
            self.assertEqual('Test OK', response.data.decode())


def create_components():
    observer = MagicMock(spec=BaseObserver)
    config = ServerConfig(
        ['*:0'], Path(f'{TEST_RESOURCE_ROOT}/keys/localhost.crt'), Path(f'{TEST_RESOURCE_ROOT}/keys/localhost.key'))
    return observer, config


if __name__ == '__main__':
    unittest.main()
