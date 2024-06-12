import os
import unittest
from importlib.metadata import version
from unittest import TestCase

from context_logger import setup_logging

from apt_repository.aptRepository import LinkedPoolAptRepository
from tests import delete_directory, create_test_packages, compare_files, compare_lines, fill_template, \
    TEST_RESOURCE_ROOT, REPOSITORY_DIR, RESOURCE_ROOT

APPLICATION_NAME = 'apt-server'
ARCHITECTURE = 'amd64'
PACKAGE_DIR = f'{TEST_RESOURCE_ROOT}/test-debs'
TEMPLATE_PATH = f'{TEST_RESOURCE_ROOT}/../templates/Release.template'


class AptRepositoryTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging(APPLICATION_NAME, 'DEBUG', warn_on_overwrite=False)
        delete_directory(PACKAGE_DIR)
        create_test_packages(PACKAGE_DIR)

    def setUp(self):
        print()

    def test_repository_tree_created_when_missing(self):
        # Given
        delete_directory(REPOSITORY_DIR)

        # When
        LinkedPoolAptRepository(APPLICATION_NAME, [ARCHITECTURE], REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH).create()

        # Then
        self.assertTrue(os.path.isdir(REPOSITORY_DIR))
        self.assertTrue(os.path.islink(f'{REPOSITORY_DIR}/pool/main'))
        self.assertTrue(os.path.isdir(f'{REPOSITORY_DIR}/dists/stable/main/binary-all'))
        self.assertTrue(os.path.isdir(f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}'))

    def test_package_dir_created_when_missing(self):
        # Given
        delete_directory(PACKAGE_DIR)

        # When
        LinkedPoolAptRepository(APPLICATION_NAME, [ARCHITECTURE], REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH).create()

        # Then
        self.assertTrue(os.path.isdir(PACKAGE_DIR))
        self.assertTrue(os.path.islink(f'{REPOSITORY_DIR}/pool/main'))
        self.assertTrue(os.path.isdir(f'{REPOSITORY_DIR}/dists/stable/main/binary-all'))
        self.assertTrue(os.path.isdir(f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}'))

        create_test_packages(PACKAGE_DIR)

    def test_packages_files_generated(self):
        # Given
        expected_path = f'{TEST_RESOURCE_ROOT}/expected/Packages'

        # When
        LinkedPoolAptRepository(APPLICATION_NAME, [ARCHITECTURE], REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH).create()

        # Then
        self.assertTrue(os.path.isdir(REPOSITORY_DIR))
        self.assertTrue(os.path.islink(f'{REPOSITORY_DIR}/pool/main'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/stable/main/binary-all/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/stable/main/binary-all/Packages.gz'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}/Packages.gz'))

        packages_path = f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}/Packages'

        exclusions = ['Size', 'MD5sum', 'SHA1', 'SHA256']
        all_matches = compare_files(expected_path, packages_path, exclusions)

        self.assertTrue(all_matches)

    def test_release_file_generated(self):
        # Given
        expected_release = fill_template(f'{RESOURCE_ROOT}/templates/Release.template',
                                         {'origin': APPLICATION_NAME,
                                          'label': APPLICATION_NAME,
                                          'version': version(APPLICATION_NAME),
                                          'architectures': 'all amd64'})

        # When
        LinkedPoolAptRepository(APPLICATION_NAME, [ARCHITECTURE], REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH).create()

        # Then
        release_file_path = f'{REPOSITORY_DIR}/dists/stable/Release'
        self.assertTrue(os.path.exists(release_file_path))

        with open(release_file_path, 'r') as release_file:
            release_content = release_file.readlines()
            exclusions = ['{{', 'Date', 'Packages']
            all_matches = compare_lines(expected_release.splitlines(True), release_content, exclusions)

        self.assertTrue(all_matches)


if __name__ == "__main__":
    unittest.main()
