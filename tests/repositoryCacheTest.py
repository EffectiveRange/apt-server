import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest import TestCase
from unittest.mock import patch

from common_utility import create_file
from context_logger import setup_logging

from package_repository import DefaultRepositoryCache
from tests import APPLICATION_NAME


class DefaultRepositoryCacheTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging(APPLICATION_NAME, 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()
        self.temp_dir = TemporaryDirectory()
        self.directory = Path(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_lock(self):
        # Given
        cache = DefaultRepositoryCache()

        # When
        cache.lock('trixie')

        # Then
        self.assertTrue(cache._distribution_locks['trixie'].locked())

    def test_unlock(self):
        # Given
        cache = DefaultRepositoryCache()

        # When
        cache.lock('trixie')
        cache.unlock('trixie')

        # Then
        self.assertFalse(cache._distribution_locks['trixie'].locked())

    def test_store_and_load(self):
        # Given
        cache = DefaultRepositoryCache()

        cache.store('trixie', self.directory / 'test.txt', b'Test content')

        # When
        loaded = cache.load('trixie', self.directory / 'test.txt')

        # Then
        self.assertEqual(loaded, b'Test content')

    def test_load_from_file_system_when_not_in_cache(self):
        # Given
        create_file(self.directory / 'test.txt', 'Test content')

        cache = DefaultRepositoryCache()

        # When
        content = cache.load('trixie', self.directory / 'test.txt')

        # Then
        self.assertEqual(content, b'Test content')

    def test_load_read_failure_when_not_in_cache(self):
        # Given
        create_file(self.directory / 'test.txt', 'Test content')

        cache = DefaultRepositoryCache()

        with patch("builtins.open", side_effect=OSError("Read failed")):
            # When
            result = cache.load('trixie', self.directory / 'test.txt')

            # Then
            self.assertIsNone(result)

    def test_store_and_clear(self):
        # Given
        cache = DefaultRepositoryCache()

        cache.store('trixie', self.directory / 'test.txt', b'Test content')

        # When
        cache.clear('trixie')

        # Then
        self.assertIsNone(cache.load('trixie', self.directory / 'test.txt'))

    def test_lock_and_clear(self):
        # Given
        cache = DefaultRepositoryCache()

        cache.store('trixie', self.directory / 'test.txt', b'Test content')

        # When
        cache.lock('trixie')
        cache.clear('trixie')

        # Then
        self.assertFalse(cache._distribution_locks['trixie'].locked())


if __name__ == "__main__":
    unittest.main()
