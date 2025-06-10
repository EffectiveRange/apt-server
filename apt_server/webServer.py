# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from dataclasses import dataclass
from threading import Thread, Lock
from typing import Any, Union

from context_logger import get_logger
from flask import Flask
from waitress.server import create_server

log = get_logger('WebServer')


@dataclass
class ServerConfig:
    listen: list[str]
    url_scheme: str
    url_prefix: str


class IWebServer(object):

    def start(self) -> None:
        raise NotImplementedError()

    def shutdown(self) -> None:
        raise NotImplementedError()

    def is_running(self) -> bool:
        raise NotImplementedError()

    def get_app(self) -> Flask:
        raise NotImplementedError()


class WebServer(IWebServer):

    def __init__(self, config: ServerConfig) -> None:
        self._app = Flask(__name__)
        self._server = create_server(self._app,
                                     listen=' '.join(config.listen),
                                     url_scheme=config.url_scheme,
                                     url_prefix=config.url_prefix)
        self._thread: Union[Thread, None] = None
        self._lock = Lock()

    def __enter__(self) -> 'WebServer':
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.shutdown()

    def start(self) -> None:
        if self._thread:
            self.shutdown()

        with self._lock:
            self._thread = Thread(target=self._start_server)
            self._thread.start()

    def shutdown(self) -> None:
        with self._lock:
            log.info('Stopping server')
            self._server.close()
            if self._thread:
                self._thread.join(1)
                self._thread = None

    def is_running(self) -> bool:
        with self._lock:
            return self._thread is not None and self._thread.is_alive()

    def get_app(self) -> Flask:
        return self._app

    def _start_server(self) -> None:
        try:
            log.info('Starting server')
            self._server.run()
        except Exception as error:
            log.info('Shutdown', reason=error)
