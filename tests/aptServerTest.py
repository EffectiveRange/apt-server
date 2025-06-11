import unittest
from pathlib import Path
from threading import Thread
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import IReusableTimer
from context_logger import setup_logging
from gnupg import Sign
from test_utility import wait_for_assertion
from watchdog.events import FileCreatedEvent, FileMovedEvent, FileDeletedEvent
from watchdog.observers.api import BaseObserver

from apt_repository import AptRepository, AptSigner, GpgException
from apt_server import AptServer, IDirectoryService, AptServerConfig


class AptServerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('apt-server', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        timer, apt_repository, apt_signer, observer, directory_service, config = create_components()

        with AptServer(timer, apt_repository, apt_signer, observer, directory_service, config) as apt_server:
            # When
            Thread(target=apt_server.run).start()

            # Then
            wait_for_assertion(1, lambda: directory_service.start.assert_called_once())
            apt_repository.create.assert_called_once()
            apt_signer.sign.assert_called_once()
            observer.schedule.assert_called_once_with(apt_server, 'path/to/packages', recursive=True)
            observer.start.assert_called_once()

        observer.stop.assert_called_once()
        timer.cancel.assert_called_once()
        directory_service.shutdown.assert_called_once()

    def test_timer_started_when_new_package_added(self):
        # Given
        timer, apt_repository, apt_signer, observer, directory_service, config = create_components()
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, config)
        event = FileCreatedEvent('path/to/packages/new-package.deb')

        # When
        apt_server.on_created(event)

        # Then
        timer.start.assert_called_once_with(config.repo_create_delay, apt_server._create_repository)

    def test_timer_restarted_when_new_package_added_and_timer_is_running(self):
        # Given
        timer, apt_repository, apt_signer, observer, directory_service, config = create_components()
        timer.is_alive.return_value = True
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, config)
        event = FileCreatedEvent('path/to/packages/new-package.deb')

        # When
        apt_server.on_created(event)

        # Then
        timer.restart.assert_called_once()

    def test_timer_started_when_package_renamed(self):
        # Given
        timer, apt_repository, apt_signer, observer, directory_service, config = create_components()
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, config)
        event = FileMovedEvent('path/to/packages/renamed-package.deb')

        # When
        apt_server.on_moved(event)

        # Then
        timer.start.assert_called_once_with(config.repo_create_delay, apt_server._create_repository)

    def test_timer_started_when_package_removed(self):
        # Given
        timer, apt_repository, apt_signer, observer, directory_service, config = create_components()
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, config)
        event = FileDeletedEvent('path/to/packages/removed-package.deb')

        # When
        apt_server.on_deleted(event)

        # Then
        timer.start.assert_called_once_with(config.repo_create_delay, apt_server._create_repository)

    def test_no_operation_when_non_package_file_added(self):
        # Given
        timer, apt_repository, apt_signer, observer, directory_service, config = create_components()
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, config)
        event = FileCreatedEvent('path/to/packages/new-file.tar.gz')

        # When
        apt_server.on_created(event)

        # Then
        timer.start.assert_not_called()

    def test_no_operation_when_shut_down(self):
        # Given
        timer, apt_repository, apt_signer, observer, directory_service, config = create_components()
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, config)

        apt_server.shutdown()

        # When
        apt_server._create_repository()

        # Then
        apt_repository.create.assert_not_called()
        apt_signer.sign.assert_not_called()

    def test_error_handled_when_create_repository_failed(self):
        # Given
        timer, apt_repository, apt_signer, observer, directory_service, config = create_components()
        apt_repository.create.side_effect = Exception('Repository creation failed')
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, config)

        # When
        apt_server._create_repository()

        # Then
        apt_repository.create.assert_called_once()
        apt_signer.sign.assert_not_called()

    def test_error_handled_when_sign_repository_failed(self):
        # Given
        timer, apt_repository, apt_signer, observer, directory_service, config = create_components()
        sign = MagicMock(spec=Sign)
        sign.returncode = 1
        sign.status = 'key expired'
        sign.stderr = 'GPG key expired at 2023-10-01'
        apt_signer.sign.side_effect = GpgException('Repository signing failed', sign)
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, config)

        # When
        apt_server._create_repository()

        # Then
        apt_repository.create.assert_called_once()
        apt_signer.sign.assert_called_once()


def create_components():
    timer = MagicMock(spec=IReusableTimer)
    timer.is_alive.return_value = False
    apt_repository = MagicMock(spec=AptRepository)
    apt_signer = MagicMock(spec=AptSigner)
    observer = MagicMock(spec=BaseObserver)
    directory_service = MagicMock(spec=IDirectoryService)
    config = AptServerConfig(Path('path/to/packages'), 0)
    return timer, apt_repository, apt_signer, observer, directory_service, config


if __name__ == "__main__":
    unittest.main()
