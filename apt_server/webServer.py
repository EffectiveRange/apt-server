# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from pathlib import Path
from ssl import SSLContext, PROTOCOL_TLS_SERVER
from threading import Thread, Lock
from typing import Any

from context_logger import get_logger
from flask import Flask
from waitress.server import create_server, BaseWSGIServer, MultiSocketServer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers.api import BaseObserver

log = get_logger('WebServer')


@dataclass
class ServerConfig:
    host: str
    port: int
    cert: Path
    key: Path


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

    def on_modified(self, event: FileSystemEvent) -> None:
        if event.src_path == str(self._config.cert):
            with self._lock:
                self._stop_server()
                self._thread = Thread(target=self._start_server)
                self._thread.start()

    def _start_server(self) -> None:
        try:
            log.info('Starting server')
            self._create_ssl_socket()
            if self._server:
                self._server.run()
        except Exception as error:
            log.info('Shutdown', reason=error)

    def _stop_server(self) -> None:
        log.info('Stopping server')
        if self._server:
            self._server.close()
        self._thread.join(1)

    def _create_ssl_socket(self) -> None:
        web_server = create_server(self._app, listen=f'{self._config.host}:{self._config.port}')
        wsgi_servers: list[BaseWSGIServer]

        if isinstance(web_server, MultiSocketServer):
            if isinstance(web_server.map, dict):
                wsgi_servers = [server for server in web_server.map.values() if isinstance(server, BaseWSGIServer)]
            else:
                wsgi_servers = []
        else:
            wsgi_servers = [web_server]

        for server in wsgi_servers:
            if server.socket:
                ssl_context = SSLContext(PROTOCOL_TLS_SERVER)
                ssl_context.load_cert_chain(certfile=self._config.cert, keyfile=self._config.key)
                server.socket = ssl_context.wrap_socket(server.socket, server_side=True)

        self._server = web_server
