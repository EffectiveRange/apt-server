import unittest
from http.server import HTTPServer
from unittest import TestCase
from unittest.mock import MagicMock

from context_logger import setup_logging
from watchdog.events import FileCreatedEvent, FileMovedEvent, FileDeletedEvent
from watchdog.observers.api import BaseObserver

from apt_repository import AptRepository, AptSigner
from apt_server import AptServer


class AptServerTest(TestCase):

    @classmethod
    def setUpClass(cls):
        setup_logging('apt-server', 'DEBUG', warn_on_overwrite=False)

    def setUp(self):
        print()

    def test_startup_and_shutdown(self):
        # Given
        deb_package_dir = 'path/to/packages'
        apt_repository, apt_signer, observer, web_server = create_mocks()

        with AptServer(apt_repository, apt_signer, observer, web_server, deb_package_dir) as apt_server:
            # When
            apt_server.run()

            # Then
            apt_repository.create.assert_called_once()
            apt_signer.sign.assert_called_once()
            observer.schedule.assert_called_once_with(apt_server, deb_package_dir, recursive=True)
            observer.start.assert_called_once()
            web_server.serve_forever.assert_called_once()

        observer.stop.assert_called_once()
        web_server.shutdown.assert_called_once()

    def test_repository_recreated_when_new_package_added(self):
        # Given
        deb_package_dir = 'path/to/packages'
        apt_repository, apt_signer, observer, web_server = create_mocks()
        apt_server = AptServer(apt_repository, apt_signer, observer, web_server, deb_package_dir)
        event = FileCreatedEvent(f'{deb_package_dir}/new-package.deb')

        # When
        apt_server.on_created(event)

        # Then
        apt_repository.create.assert_called_once()
        apt_signer.sign.assert_called_once()

    def test_repository_recreated_when_package_renamed(self):
        # Given
        deb_package_dir = 'path/to/packages'
        apt_repository, apt_signer, observer, web_server = create_mocks()
        apt_server = AptServer(apt_repository, apt_signer, observer, web_server, deb_package_dir)
        event = FileMovedEvent(f'{deb_package_dir}/renamed-package.deb')

        # When
        apt_server.on_moved(event)

        # Then
        apt_repository.create.assert_called_once()
        apt_signer.sign.assert_called_once()

    def test_repository_recreated_when_package_removed(self):
        # Given
        deb_package_dir = 'path/to/packages'
        apt_repository, apt_signer, observer, web_server = create_mocks()
        apt_server = AptServer(apt_repository, apt_signer, observer, web_server, deb_package_dir)
        event = FileDeletedEvent(f'{deb_package_dir}/removed-package.deb')

        # When
        apt_server.on_deleted(event)

        # Then
        apt_repository.create.assert_called_once()
        apt_signer.sign.assert_called_once()

    def test_no_operation_when_non_package_file_added(self):
        # Given
        deb_package_dir = 'path/to/packages'
        apt_repository, apt_signer, observer, web_server = create_mocks()
        apt_server = AptServer(apt_repository, apt_signer, observer, web_server, deb_package_dir)
        event = FileCreatedEvent(f'{deb_package_dir}/new-file.tar.gz')

        # When
        apt_server.on_created(event)

        # Then
        apt_repository.create.assert_not_called()
        apt_signer.sign.assert_not_called()


def create_mocks():
    apt_repository = MagicMock(spec=AptRepository)
    apt_signer = MagicMock(spec=AptSigner)
    observer = MagicMock(spec=BaseObserver)
    web_server = MagicMock(spec=HTTPServer)
    return apt_repository, apt_signer, observer, web_server


if __name__ == "__main__":
    unittest.main()
