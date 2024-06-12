# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from http.server import HTTPServer
from threading import Thread
from typing import Any

from context_logger import get_logger
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers.api import BaseObserver

from apt_repository import AptSigner, GpgException
from apt_repository.aptRepository import AptRepository

log = get_logger('AptServer')


class AptServer(FileSystemEventHandler):

    def __init__(self, apt_repository: AptRepository, apt_signer: AptSigner, observer: BaseObserver,
                 web_server: HTTPServer, deb_package_dir: str) -> None:
        self._apt_repository = apt_repository
        self._apt_signer = apt_signer
        self._observer = observer
        self._web_server = web_server
        self._deb_package_dir = deb_package_dir

    def __enter__(self) -> 'AptServer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def run(self) -> None:
        log.info('Creating initial repository')
        self._apt_repository.create()

        log.info('Signing initial repository')
        self._sign_repository()

        log.info('Watching directory for .deb file changes', directory=self._deb_package_dir)
        self._observer.schedule(self, self._deb_package_dir)

        log.info('Starting component', component='file-observer')
        self._observer.start()

        log.info('Starting component', component='web-server')
        self._web_server.serve_forever()

    def shutdown(self) -> None:
        self._observer.stop()
        Thread(target=self._web_server.shutdown).start()

    def on_created(self, event: FileSystemEvent) -> None:
        self._on_changed(event)

    def on_moved(self, event: FileSystemEvent) -> None:
        self._on_changed(event)

    def on_deleted(self, event: FileSystemEvent) -> None:
        self._on_changed(event)

    def _on_changed(self, event: FileSystemEvent) -> None:
        if event.src_path.endswith('.deb'):
            log.info('File change event, recreating repository', event_type=event.event_type, file=event.src_path)
            self._apt_repository.create()
            self._sign_repository()
        else:
            log.info('File change event, ignoring as not a package', event_type=event.event_type, file=event.src_path)

    def _sign_repository(self) -> None:
        try:
            self._apt_signer.sign()
        except GpgException as exception:
            log.error('Error signing repository', operation=exception.operation, code=exception.code,
                      status=exception.status, error=exception.error)
