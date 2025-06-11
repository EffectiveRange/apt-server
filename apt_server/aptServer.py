# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import Path
from threading import Thread, Event, Lock
from typing import Any

from common_utility import IReusableTimer
from context_logger import get_logger
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers.api import BaseObserver

from apt_repository import AptSigner, GpgException
from apt_repository.aptRepository import AptRepository
from apt_server import IDirectoryService

log = get_logger('AptServer')


@dataclass
class AptServerConfig:
    deb_package_dir: Path
    repo_create_delay: float


class AptServer(FileSystemEventHandler):

    def __init__(self, timer: IReusableTimer, apt_repository: AptRepository, apt_signer: AptSigner,
                 file_observer: BaseObserver, directory_service: IDirectoryService, config: AptServerConfig) -> None:
        self._timer = timer
        self._apt_repository = apt_repository
        self._apt_signer = apt_signer
        self._file_observer = file_observer
        self._directory_service = directory_service
        self._config = config
        self._shutdown_event = Event()
        self._repository_lock = Lock()

    def __enter__(self) -> 'AptServer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def run(self) -> None:
        log.info('Creating initial repository')
        self._create_repository()

        deb_package_dir = str(self._config.deb_package_dir)
        log.info('Watching directory for .deb file changes', directory=deb_package_dir)
        self._file_observer.schedule(self, deb_package_dir, recursive=True)

        log.info('Starting component', component='file-observer')
        self._file_observer.start()

        log.info('Starting component', component='directory-service')
        self._directory_service.start()

        self._shutdown_event.wait()

    def shutdown(self) -> None:
        self._file_observer.stop()
        self._timer.cancel()
        Thread(target=self._directory_service.shutdown).start()
        self._shutdown_event.set()

    def on_created(self, event: FileSystemEvent) -> None:
        self._on_changed(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._on_changed(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._on_changed(event)

    def _on_changed(self, event: FileSystemEvent) -> None:
        if str(event.src_path).endswith('.deb'):
            log.info('File change event, recreating repository', event_type=event.event_type, file=event.src_path)
            if self._timer.is_alive():
                self._timer.restart()
            else:
                self._timer.start(self._config.repo_create_delay, self._create_repository)
        else:
            log.info('File change event, ignoring as not a package', event_type=event.event_type, file=event.src_path)

    def _create_repository(self) -> None:
        if self._shutdown_event.is_set():
            return

        with self._repository_lock:
            try:
                self._apt_repository.create()
                self._apt_signer.sign()
            except GpgException as exception:
                log.error('Error signing repository', operation=exception.operation, code=exception.code,
                          status=exception.status, error=exception.error)
            except Exception as exception:
                log.error('Error creating repository', error=exception)
