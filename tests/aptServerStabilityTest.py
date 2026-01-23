import unittest
from threading import Thread
from unittest import TestCase

import requests
from context_logger import setup_logging


class AptServerStabilityTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('apt-server', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_http_server_with_multiple_concurrent_requests(self):
        # Given
        request_count = 100
        timeout = 10
        threads = []
        responses = []

        def send_request():
            try:
                response = requests.get(
                    'http://aptrepo.effective-range.com/pool/main/trixie/trixie_libzmq-drafts_4.3.6-1_amd64.deb',
                    timeout=timeout)
                responses.append(response)
            except requests.exceptions.RequestException as e:
                print(f'Exception raised: {e}')

        # When
        for index in range(request_count):
            thread = Thread(target=lambda: send_request())
            threads.append(thread)
            thread.start()

        # Then
        for thread in threads:
            thread.join(timeout)
        self.assertEqual(request_count, len(responses))
        for response in responses:
            self.assertEqual(200, response.status_code)


if __name__ == "__main__":
    unittest.main()
