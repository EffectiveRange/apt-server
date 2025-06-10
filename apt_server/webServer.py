# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import Path
from ssl import SSLContext, PROTOCOL_TLS_SERVER
from threading import Thread, Lock
from typing import Any, Optional

from context_logger import get_logger
from flask import Flask
from waitress.server import create_server, BaseWSGIServer, MultiSocketServer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers.api import BaseObserver

log = get_logger('WebServer')


@dataclass
class ServerConfig:
    listen: list[str]
    cert: Optional[Path]
    key: Optional[Path]


class IWebServer(object):

    def start(self) -> None:
        raise NotImplementedError()

    def shutdown(self) -> None:
        raise NotImplementedError()

    def get_app(self) -> Flask:
        raise NotImplementedError()


class WebServer(IWebServer, FileSystemEventHandler):

    def __init__(self, observer: BaseObserver, config: ServerConfig) -> None:
        self._observer = observer
        self._config = config
        self._app = Flask(__name__)
        self._server: MultiSocketServer | BaseWSGIServer | None = None

        self._thread = Thread(target=self._start_server)
        self._lock = Lock()

        if self._config.cert and self._config.key:
            self._observer.schedule(self, str(self._config.cert.parent), recursive=True)

    def __enter__(self) -> 'WebServer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def start(self) -> None:
        with self._lock:
            self._thread = Thread(target=self._start_server)
            self._thread.start()
            self._observer.start()

    def shutdown(self) -> None:
        with self._lock:
            log.info('Shutting down')
            self._observer.stop()
            self._stop_server()

    def get_app(self) -> Flask:
        return self._app

    def on_closed(self, event: FileSystemEvent) -> None:
        if event.src_path == str(self._config.cert):
            with self._lock:
                log.info('Certificate file modified, restarting server')
                self._stop_server()
                self._thread = Thread(target=self._start_server)
                self._thread.start()

    def _start_server(self) -> None:
        try:
            log.info('Starting server')
            self._create_server()
            if self._server:
                self._server.run()
        except Exception as error:
            log.info('Shutdown', reason=error)

    def _stop_server(self) -> None:
        log.info('Stopping server')
        if self._server:
            self._server.close()
        self._thread.join(1)

    def _create_server(self) -> None:
        listen = ' '.join(self._config.listen)
        self._server = create_server(self._app, listen=listen)

        if self._config.cert and self._config.key:
            self._create_ssl_socket(self._config.cert, self._config.key)

    def _create_ssl_socket(self, cert: Path, key: Path) -> None:
        if not cert.is_file() or not key.is_file():
            log.error('Certificate or key file not found', cert=cert, key=key)
            return

        wsgi_servers: list[BaseWSGIServer] = []

        if isinstance(self._server, MultiSocketServer):
            if isinstance(self._server.map, dict):
                wsgi_servers = [server for server in self._server.map.values() if isinstance(server, BaseWSGIServer)]
        elif isinstance(self._server, BaseWSGIServer):
            wsgi_servers = [self._server]

        if not wsgi_servers:
            log.error('No WSGI servers found to wrap with SSL')
            return

        for server in wsgi_servers:
            if server.socket:
                ssl_context = SSLContext(PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(certfile=cert, keyfile=key)
                server.socket = ssl_context.wrap_socket(server.socket, server_side=True)
