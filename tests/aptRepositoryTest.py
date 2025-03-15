import os
import unittest
from importlib.metadata import version
from unittest import TestCase

from common_utility import delete_directory
from context_logger import setup_logging

from apt_repository.aptRepository import LinkedPoolAptRepository
from tests import (
    create_test_packages,
    fill_template,
    TEST_RESOURCE_ROOT,
    REPOSITORY_DIR,
    RESOURCE_ROOT,
    compare_lines,
)

APPLICATION_NAME = 'apt-server'
ARCHITECTURE = 'amd64'
DISTRIBUTION = 'stable'
PACKAGE_DIR = f'{TEST_RESOURCE_ROOT}/test-debs'
TEMPLATE_PATH = f'{TEST_RESOURCE_ROOT}/../templates/Release.template'


class AptRepositoryTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging(APPLICATION_NAME, 'DEBUG', warn_on_overwrite=False)
        delete_directory(PACKAGE_DIR)
        create_test_packages(PACKAGE_DIR, DISTRIBUTION)

    def setUp(self):
        print()

    def test_repository_tree_created_when_missing(self):
        # Given
        delete_directory(REPOSITORY_DIR)

        repository = LinkedPoolAptRepository(
            APPLICATION_NAME, {ARCHITECTURE}, set(), REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH
        )

        # When
        repository.create()

        # Then
        self.assertTrue(os.path.isdir(REPOSITORY_DIR))
        self.assertTrue(os.path.islink(f'{REPOSITORY_DIR}/pool/main'))
        self.assertTrue(os.path.isdir(f'{REPOSITORY_DIR}/dists/stable/main/binary-all'))
        self.assertTrue(os.path.isdir(f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}'))

    def test_package_dir_created_when_missing(self):
        # Given
        delete_directory(PACKAGE_DIR)

        repository = LinkedPoolAptRepository(
            APPLICATION_NAME, {ARCHITECTURE}, set(), REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH
        )

        # When
        repository.create()

        # Then
        self.assertTrue(os.path.isdir(PACKAGE_DIR))
        self.assertTrue(os.path.islink(f'{REPOSITORY_DIR}/pool/main'))
        self.assertTrue(os.path.isdir(f'{REPOSITORY_DIR}/dists/stable/main/binary-all'))
        self.assertTrue(os.path.isdir(f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}'))

        create_test_packages(PACKAGE_DIR, DISTRIBUTION)

    def test_packages_files_generated(self):
        # Given
        expected_packages = fill_template(
            f'{TEST_RESOURCE_ROOT}/expected/Packages.template',
            {'architecture': 'amd64', 'distribution': DISTRIBUTION},
        ).splitlines()

        repository = LinkedPoolAptRepository(
            APPLICATION_NAME, {'amd64'}, set(), REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH
        )

        # When
        repository.create()

        # Then
        self.assertTrue(os.path.isdir(REPOSITORY_DIR))
        self.assertTrue(os.path.islink(f'{REPOSITORY_DIR}/pool/main'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/stable/main/binary-all/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/stable/main/binary-all/Packages.gz'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}/Packages.gz'))

        packages_path = f'{REPOSITORY_DIR}/dists/stable/main/binary-{ARCHITECTURE}/Packages'
        packages = open(packages_path, 'r').read().splitlines()

        exclusions = ['Size', 'MD5sum', 'SHA1', 'SHA256']
        all_matches = compare_lines(expected_packages, packages, exclusions)

        self.assertTrue(all_matches)

    def test_packages_files_generated_when_multiple_distributions(self):
        # Given
        delete_directory(PACKAGE_DIR)
        create_test_packages(PACKAGE_DIR, 'bullseye')
        create_test_packages(PACKAGE_DIR, 'bookworm')

        expected_packages_bullseye = fill_template(
            f'{TEST_RESOURCE_ROOT}/expected/Packages.template',
            {'architecture': 'amd64', 'distribution': 'bullseye'},
        ).splitlines()
        expected_packages_bookworm = fill_template(
            f'{TEST_RESOURCE_ROOT}/expected/Packages.template',
            {'architecture': 'amd64', 'distribution': 'bookworm'},
        ).splitlines()

        repository = LinkedPoolAptRepository(
            APPLICATION_NAME, {'amd64'}, {'bullseye', 'bookworm'}, REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH
        )

        # When
        repository.create()

        # Then
        self.assertTrue(os.path.isdir(REPOSITORY_DIR))
        self.assertTrue(os.path.islink(f'{REPOSITORY_DIR}/pool/main'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/bullseye/main/binary-all/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/bullseye/main/binary-all/Packages.gz'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/bullseye/main/binary-amd64/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/bullseye/main/binary-amd64/Packages.gz'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/bookworm/main/binary-all/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/bookworm/main/binary-all/Packages.gz'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/bookworm/main/binary-amd64/Packages'))
        self.assertTrue(os.path.isfile(f'{REPOSITORY_DIR}/dists/bookworm/main/binary-amd64/Packages.gz'))

        packages_bullseye = open(f'{REPOSITORY_DIR}/dists/bullseye/main/binary-amd64/Packages', 'r').read().splitlines()
        packages_bookworm = open(f'{REPOSITORY_DIR}/dists/bookworm/main/binary-amd64/Packages', 'r').read().splitlines()

        exclusions = ['Size', 'MD5sum', 'SHA1', 'SHA256']

        all_matches = compare_lines(expected_packages_bullseye, packages_bullseye, exclusions)
        self.assertTrue(all_matches)
        all_matches = compare_lines(expected_packages_bookworm, packages_bookworm, exclusions)
        self.assertTrue(all_matches)

    def test_release_file_generated(self):
        # Given
        expected_release = fill_template(
            f'{RESOURCE_ROOT}/templates/Release.template',
            {
                'origin': APPLICATION_NAME,
                'label': APPLICATION_NAME,
                'codename': 'stable',
                'version': version(APPLICATION_NAME),
                'architectures': 'all amd64',
            },
        ).splitlines()

        repository = LinkedPoolAptRepository(
            APPLICATION_NAME, {ARCHITECTURE}, set(), REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH
        )

        # When
        repository.create()

        # Then
        release_file_path = f'{REPOSITORY_DIR}/dists/stable/Release'
        self.assertTrue(os.path.exists(release_file_path))

        release = open(release_file_path, 'r').read().splitlines()

        exclusions = ['{{', 'Date', 'Packages']

        all_matches = compare_lines(expected_release, release, exclusions)
        self.assertTrue(all_matches)

    def test_release_files_generated_when_multiple_distributions(self):
        # Given
        expected_release_bullseye = fill_template(
            f'{RESOURCE_ROOT}/templates/Release.template',
            {
                'origin': APPLICATION_NAME,
                'label': APPLICATION_NAME,
                'codename': 'bullseye',
                'version': version(APPLICATION_NAME),
                'architectures': 'all amd64',
            },
        ).splitlines()
        expected_release_bookworm = fill_template(
            f'{RESOURCE_ROOT}/templates/Release.template',
            {
                'origin': APPLICATION_NAME,
                'label': APPLICATION_NAME,
                'codename': 'bookworm',
                'version': version(APPLICATION_NAME),
                'architectures': 'all amd64',
            },
        ).splitlines()

        repository = LinkedPoolAptRepository(
            APPLICATION_NAME, {ARCHITECTURE}, set(), REPOSITORY_DIR, PACKAGE_DIR, TEMPLATE_PATH
        )

        # When
        repository.create()

        # Then
        release_bullseye_path = f'{REPOSITORY_DIR}/dists/bullseye/Release'
        self.assertTrue(os.path.exists(release_bullseye_path))
        release_bookworm_path = f'{REPOSITORY_DIR}/dists/bookworm/Release'
        self.assertTrue(os.path.exists(release_bookworm_path))

        release_bullseye = open(release_bullseye_path, 'r').read().splitlines()
        release_bookworm = open(release_bookworm_path, 'r').read().splitlines()

        exclusions = ['{{', 'Date', 'Packages']

        all_matches = compare_lines(expected_release_bullseye, release_bullseye, exclusions)
        self.assertTrue(all_matches)

        all_matches = compare_lines(expected_release_bookworm, release_bookworm, exclusions)
        self.assertTrue(all_matches)


if __name__ == "__main__":
    unittest.main()
