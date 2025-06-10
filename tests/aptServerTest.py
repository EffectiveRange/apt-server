import unittest
from pathlib import Path
from threading import Thread
from unittest import TestCase
from unittest.mock import MagicMock

from common_utility import IReusableTimer
from context_logger import setup_logging
from test_utility import wait_for_assertion
from watchdog.events import FileCreatedEvent, FileMovedEvent, FileDeletedEvent
from watchdog.observers.api import BaseObserver

from apt_repository import AptRepository, AptSigner
from apt_server import AptServer, IDirectoryService


class AptServerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('apt-server', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        deb_package_dir = Path('path/to/packages')
        timer, apt_repository, apt_signer, observer, directory_service = create_mocks()

        with AptServer(timer, apt_repository, apt_signer, observer, directory_service, deb_package_dir) as apt_server:
            # When
            Thread(target=apt_server.run).start()

            # Then
            wait_for_assertion(1, lambda: directory_service.start.assert_called_once())
            timer.start.assert_called_once()
            observer.schedule.assert_called_once_with(apt_server, str(deb_package_dir), recursive=True)
            observer.start.assert_called_once()

        observer.stop.assert_called_once()
        directory_service.shutdown.assert_called_once()

    def test_repository_recreated_when_new_package_added(self):
        # Given
        deb_package_dir = Path('path/to/packages')
        timer, apt_repository, apt_signer, observer, directory_service = create_mocks()
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, deb_package_dir)
        event = FileCreatedEvent(f'{deb_package_dir}/new-package.deb')

        # When
        apt_server.on_created(event)

        # Then
        timer.restart.assert_called_once()

    def test_repository_recreated_when_package_renamed(self):
        # Given
        deb_package_dir = Path('path/to/packages')
        timer, apt_repository, apt_signer, observer, directory_service = create_mocks()
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, deb_package_dir)
        event = FileMovedEvent(f'{deb_package_dir}/renamed-package.deb')

        # When
        apt_server.on_moved(event)

        # Then
        timer.restart.assert_called_once()

    def test_repository_recreated_when_package_removed(self):
        # Given
        deb_package_dir = Path('path/to/packages')
        timer, apt_repository, apt_signer, observer, directory_service = create_mocks()
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, deb_package_dir)
        event = FileDeletedEvent(f'{deb_package_dir}/removed-package.deb')

        # When
        apt_server.on_deleted(event)

        # Then
        timer.restart.assert_called_once()

    def test_no_operation_when_non_package_file_added(self):
        # Given
        deb_package_dir = Path('path/to/packages')
        timer, apt_repository, apt_signer, observer, directory_service = create_mocks()
        apt_server = AptServer(timer, apt_repository, apt_signer, observer, directory_service, deb_package_dir)
        event = FileCreatedEvent(f'{deb_package_dir}/new-file.tar.gz')

        # When
        apt_server.on_created(event)

        # Then
        apt_repository.create.assert_not_called()
        apt_signer.sign.assert_not_called()


def create_mocks():
    timer = MagicMock(spec=IReusableTimer)
    apt_repository = MagicMock(spec=AptRepository)
    apt_signer = MagicMock(spec=AptSigner)
    observer = MagicMock(spec=BaseObserver)
    directory_service = MagicMock(spec=IDirectoryService)
    return timer, apt_repository, apt_signer, observer, directory_service


if __name__ == "__main__":
    unittest.main()
