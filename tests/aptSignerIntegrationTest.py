import os
import unittest
from collections import deque
from unittest import TestCase

from common_utility import delete_directory
from context_logger import setup_logging
from gnupg import GPG

from apt_repository.aptRepository import LinkedPoolAptRepository
from apt_repository.aptSigner import ReleaseSigner, GpgKey
from tests import create_test_packages, TEST_RESOURCE_ROOT, RESOURCE_ROOT, REPOSITORY_DIR

APPLICATION_NAME = 'apt-server'
ARCHITECTURE = 'amd64'
DISTRIBUTION = 'stable'
PACKAGE_DIR = f'{TEST_RESOURCE_ROOT}/test-debs'
TEMPLATE_PATH = f'{RESOURCE_ROOT}/templates/Release.template'
PRIVATE_KEY_PATH = f'{TEST_RESOURCE_ROOT}/keys/private-key.asc'
PUBLIC_KEY_PATH = f'{TEST_RESOURCE_ROOT}/keys/public-key.asc'
KEY_ID = 'C1AEE2EDBAEC37595801DDFAE15BC62117A4E0F3'
PASSPHRASE = 'test1234'


class AptSignerIntegrationTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging(APPLICATION_NAME, 'DEBUG', warn_on_overwrite=False)
        delete_directory(PACKAGE_DIR)
        create_test_packages(PACKAGE_DIR, DISTRIBUTION)

    def setUp(self):
        print()
        delete_directory(REPOSITORY_DIR)

    def test_release_file_signed(self):
        # Given
        gpg, public_key, private_key = create_components()
        release_signer = ReleaseSigner(gpg, public_key, private_key, REPOSITORY_DIR)

        LinkedPoolAptRepository(
            APPLICATION_NAME, {ARCHITECTURE}, {DISTRIBUTION}, REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH
        ).create()

        # When
        release_signer.sign()

        # Then
        release_path = f'{REPOSITORY_DIR}/dists/stable'
        release_file_path = f'{release_path}/Release'
        self.assertTrue(os.path.exists(release_file_path))

        with open(release_file_path) as release_file:
            last_line = deque(release_file, 1)[0]
            self.assertEqual(last_line, f'SignWith: {KEY_ID}')

        signed_release_file_path = f'{release_path}/InRelease'
        self.assertTrue(os.path.exists(signed_release_file_path))

        signature_file_path = f'{release_path}/Release.gpg'
        self.assertTrue(os.path.exists(signature_file_path))

        with (
            open(PUBLIC_KEY_PATH, 'rb') as public_key_file,
            open(f'{release_path}/public.key', 'rb') as verification_key_file,
        ):
            self.assertEqual(public_key_file.read(), verification_key_file.read())

    def test_release_file_resigned(self):
        # Given
        gpg, public_key, private_key = create_components()
        release_signer = ReleaseSigner(gpg, public_key, private_key, REPOSITORY_DIR)

        LinkedPoolAptRepository(
            APPLICATION_NAME, {ARCHITECTURE}, {DISTRIBUTION}, REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH
        ).create()
        release_signer.sign()

        release_path = f'{REPOSITORY_DIR}/dists/stable'
        release_file_path = f'{release_path}/Release'

        with open(release_file_path, 'a') as release_file:
            release_file.write('\nSignWith: ABCDEFGHIJKLMNOPQRSTUVWXYZ')

        # When
        release_signer.sign()

        # Then
        with open(release_file_path) as release_file:
            last_line = deque(release_file, 1)[0]
            self.assertEqual(last_line, f'SignWith: {KEY_ID}')


def create_components():
    gpg = GPG()
    public_key = GpgKey(KEY_ID, PUBLIC_KEY_PATH)
    private_key = GpgKey(KEY_ID, PRIVATE_KEY_PATH, PASSPHRASE)

    return gpg, public_key, private_key


if __name__ == "__main__":
    unittest.main()
