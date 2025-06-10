import unittest
from unittest import TestCase

from context_logger import setup_logging
from flask import Response
from test_utility import wait_for_condition

from apt_server import WebServer, ServerConfig


class ApiServerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('er-scarecrow-server', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        config = ServerConfig(['*:0'], 'http', '')

        with WebServer(config) as web_server:
            # When
            web_server.start()

            # Then
            wait_for_condition(1, lambda: web_server.is_running())

        wait_for_condition(1, lambda: not web_server.is_running())

    def test_returns_200(self):
        # Given
        config = ServerConfig(['*:0'], 'http', '')

        with WebServer(config) as web_server:
            # When
            @web_server.get_app().route('/test', methods=['GET'])
            def get_test() -> Response:
                return Response(status=200, response='Test OK')

            web_server.start()

            wait_for_condition(1, lambda: web_server.is_running())

            client = web_server._app.test_client()

            # When
            response = client.get('/test')

            # Then
            self.assertEqual(200, response.status_code)
            self.assertEqual('Test OK', response.data.decode())


if __name__ == '__main__':
    unittest.main()
