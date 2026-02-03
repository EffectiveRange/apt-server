import unittest
from unittest import TestCase
from unittest.mock import MagicMock, call

from context_logger import setup_logging
from test_utility import wait_for_assertion

from package_repository import PackageWatcher, RepositoryCreator, RepositorySigner, RepositoryCache, \
    DefaultRepositoryService
from tests import APPLICATION_NAME


class RepositoryServiceTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging(APPLICATION_NAME, 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_start(self):
        # Given
        watcher, creator, signer, cache = create_components()
        service = DefaultRepositoryService(watcher, creator, signer, cache, {'bookworm', 'trixie'}, 0.1)

        # When
        service.start()

        # Then
        creator.initialize.assert_called_once()
        creator.create.assert_has_calls([call('bookworm'), call('trixie')], any_order=True)
        signer.initialize.assert_called_once()
        signer.sign.assert_has_calls([call('bookworm'), call('trixie')], any_order=True)
        watcher.register.assert_called_once_with(service._handle_event)
        watcher.start.assert_called_once()
        cache.lock.assert_has_calls([call('bookworm'), call('trixie')], any_order=True)
        cache.clear.assert_has_calls([call('bookworm'), call('trixie')], any_order=True)

    def test_stop(self):
        # Given
        watcher, creator, signer, cache = create_components()
        service = DefaultRepositoryService(watcher, creator, signer, cache, {'bookworm', 'trixie'}, 0.1)

        # When
        service.stop()

        # Then
        watcher.deregister.assert_called_once_with(service._handle_event)
        watcher.stop.assert_called_once()

    def test_event_handled(self):
        # Given
        watcher, creator, signer, cache = create_components()
        service = DefaultRepositoryService(watcher, creator, signer, cache, {'bookworm', 'trixie'}, 0.1)

        # When
        service._handle_event('trixie')

        # Then
        wait_for_assertion(1, lambda: cache.lock.assert_called_once_with('trixie'))
        creator.create.assert_called_once_with('trixie')
        signer.sign.assert_called_once_with('trixie')
        cache.clear.assert_called_once_with('trixie')

    def test_event_handled_when_another_event_is_handled(self):
        # Given
        watcher, creator, signer, cache = create_components()
        service = DefaultRepositoryService(watcher, creator, signer, cache, {'bookworm', 'trixie'}, 0.1)

        service._handle_event('trixie')

        # When
        service._handle_event('trixie')

        # Then
        wait_for_assertion(1, lambda: cache.lock.assert_called_once_with('trixie'))
        creator.create.assert_called_once_with('trixie')
        signer.sign.assert_called_once_with('trixie')
        cache.clear.assert_called_once_with('trixie')

    def test_event_not_handled_when_unsupported(self):
        # Given
        watcher, creator, signer, cache = create_components()
        service = DefaultRepositoryService(watcher, creator, signer, cache, {'bookworm', 'trixie'}, 0.1)

        # When
        service._handle_event('unsupported')

        # Then
        creator.create.assert_not_called()
        signer.sign.assert_not_called()
        cache.lock.assert_not_called()
        cache.clear.assert_not_called()


def create_components():
    watcher = MagicMock(spec=PackageWatcher)
    creator = MagicMock(spec=RepositoryCreator)
    signer = MagicMock(spec=RepositorySigner)
    cache = MagicMock(spec=RepositoryCache)

    return watcher, creator, signer, cache


if __name__ == "__main__":
    unittest.main()
