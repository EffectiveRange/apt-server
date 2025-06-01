# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from pathlib import Path
from threading import Thread, Event
from typing import Any

from common_utility import IReusableTimer
from context_logger import get_logger
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers.api import BaseObserver

from apt_repository import AptSigner, GpgException
from apt_repository.aptRepository import AptRepository
from apt_server import WebServer

log = get_logger('AptServer')


class AptServer(FileSystemEventHandler):

    def __init__(self, timer: IReusableTimer, apt_repository: AptRepository, apt_signer: AptSigner,
                 observer: BaseObserver, web_server: WebServer, deb_package_dir: Path, delay: float = 5) -> None:
        self._timer = timer
        self._apt_repository = apt_repository
        self._apt_signer = apt_signer
        self._observer = observer
        self._web_server = web_server
        self._deb_package_dir = deb_package_dir
        self._delay = delay
        self._event = Event()

    def __enter__(self) -> 'AptServer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def run(self) -> None:
        log.info('Creating initial repository')
        self._timer.start(self._delay, self._create_repository)

        log.info('Watching directory for .deb file changes', directory=str(self._deb_package_dir))
        self._observer.schedule(self, str(self._deb_package_dir), recursive=True)

        log.info('Starting component', component='file-observer')
        self._observer.start()

        log.info('Starting component', component='web-server')
        self._web_server.start()

        self._event.wait()

    def shutdown(self) -> None:
        self._observer.stop()
        Thread(target=self._web_server.shutdown).start()
        self._event.set()

    def on_created(self, event: FileSystemEvent) -> None:
        self._on_changed(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._on_changed(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._on_changed(event)

    def _on_changed(self, event: FileSystemEvent) -> None:
        if str(event.src_path).endswith('.deb'):
            log.info('File change event, recreating repository', event_type=event.event_type, file=event.src_path)
            self._timer.restart()
        else:
            log.info('File change event, ignoring as not a package', event_type=event.event_type, file=event.src_path)

    def _create_repository(self) -> None:
        try:
            self._apt_repository.create()
            self._apt_signer.sign()
        except GpgException as exception:
            log.error('Error signing repository', operation=exception.operation, code=exception.code,
                      status=exception.status, error=exception.error)
        except Exception as exception:
            log.exception('Error creating repository', error=exception)
