# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from threading import Event
from typing import Any

from context_logger import get_logger

from package_repository import RepositoryService, DirectoryService

log = get_logger('RepositoryServer')


class RepositoryServer:

    def run(self) -> None:
        raise NotImplementedError()

    def shutdown(self) -> None:
        raise NotImplementedError()


class DefaultRepositoryServer(RepositoryServer):

    def __init__(self, repository_service: RepositoryService, directory_service: DirectoryService) -> None:
        self._repository_service = repository_service
        self._directory_service = directory_service
        self._shutdown_event = Event()

    def __enter__(self) -> RepositoryServer:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def run(self) -> None:
        log.info('Starting service', service='repository-service')
        self._repository_service.start()

        log.info('Starting service', service='directory-service')
        self._directory_service.start()

        self._shutdown_event.wait()

    def shutdown(self) -> None:
        self._repository_service.stop()
        self._directory_service.stop()
        self._shutdown_event.set()
