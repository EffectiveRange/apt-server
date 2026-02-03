import os
import unittest
from importlib.metadata import version
from unittest import TestCase

from common_utility import delete_directory, render_template_file, create_directory
from context_logger import setup_logging
from test_utility import compare_lines

from package_repository import RepositoryConfig, DefaultRepositoryCreator
from tests import (
    create_test_packages,
    TEST_RESOURCE_ROOT,
    REPOSITORY_DIR,
    RESOURCE_ROOT, PACKAGE_DIR, APPLICATION_NAME, RELEASE_TEMPLATE_PATH
)


class RepositoryCreatorTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging(APPLICATION_NAME, 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()
        delete_directory(PACKAGE_DIR)
        create_test_packages(PACKAGE_DIR, 'bookworm')
        create_test_packages(PACKAGE_DIR, 'trixie')
        create_directory(REPOSITORY_DIR)

    def test_initialize_when_repository_tree_is_missing(self):
        # Given
        delete_directory(REPOSITORY_DIR)

        config = create_config()
        creator = DefaultRepositoryCreator(config)

        # When
        creator.initialize()

        # Then
        self.assertTrue(os.path.isdir(REPOSITORY_DIR))
        self.assertTrue(os.path.islink(f'{REPOSITORY_DIR}/pool'))

    def test_initialize_when_package_dir_is_missing(self):
        # Given
        delete_directory(PACKAGE_DIR)

        config = create_config()
        creator = DefaultRepositoryCreator(config)

        # When
        creator.initialize()

        # Then
        self.assertTrue(os.path.isdir(PACKAGE_DIR))
        self.assertTrue(os.path.islink(f'{REPOSITORY_DIR}/pool'))

    def test_create_assert_packages_files_generated(self):
        # Given
        expected_packages = render_template_file(
            f'{TEST_RESOURCE_ROOT}/expected/Packages.template',
            {'distribution': 'trixie', 'component': 'main', 'architecture': 'amd64'},
        ).splitlines()

        config = create_config()
        creator = DefaultRepositoryCreator(config)

        # When
        creator.create('trixie')

        # Then
        self.assertTrue(os.path.isdir(REPOSITORY_DIR))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/trixie/main/binary-all/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/trixie/main/binary-all/Packages.gz'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/trixie/main/binary-amd64/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/trixie/main/binary-amd64/Packages.gz'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/trixie/main/binary-arm64/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/trixie/main/binary-arm64/Packages.gz'))

        packages_path = f'{REPOSITORY_DIR}/dists/trixie/main/binary-amd64/Packages'
        packages = open(packages_path, 'r').read().splitlines()

        exclusions = ['Size', 'MD5sum', 'SHA1', 'SHA256']
        all_matches = compare_lines(expected_packages, packages, exclusions)

        self.assertTrue(all_matches)

    def test_create_assert_release_file_generated(self):
        # Given
        expected_release = render_template_file(
            f'{RESOURCE_ROOT}/templates/Release.j2',
            {
                'origin': APPLICATION_NAME,
                'label': APPLICATION_NAME,
                'codename': 'trixie',
                'version': version(APPLICATION_NAME),
                'architectures': 'all amd64 arm64',
            },
        ).splitlines()

        config = create_config()
        creator = DefaultRepositoryCreator(config)

        # When
        creator.create('trixie')

        # Then
        release_file_path = f'{REPOSITORY_DIR}/dists/trixie/Release'
        self.assertTrue(os.path.exists(release_file_path))

        release = open(release_file_path, 'r').read().splitlines()

        exclusions = ['', 'Date', 'Packages']

        all_matches = compare_lines(expected_release, release, exclusions)
        self.assertTrue(all_matches)


def create_config():
    return RepositoryConfig(APPLICATION_NAME, '1.0.0', {'bookworm', 'trixie'}, {'main'}, {'amd64', 'arm64'},
                            REPOSITORY_DIR, PACKAGE_DIR, RELEASE_TEMPLATE_PATH)


if __name__ == "__main__":
    unittest.main()
