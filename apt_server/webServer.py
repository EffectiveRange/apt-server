# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import os
import time
from dataclasses import dataclass
from pathlib import Path
from ssl import SSLContext, PROTOCOL_TLS_SERVER
from threading import Thread, Lock
from typing import Any
from urllib.parse import quote

from context_logger import get_logger
from flask import Flask, send_from_directory, render_template_string, abort, request
from waitress.server import create_server, BaseWSGIServer, MultiSocketServer
from watchdog.events import FileSystemEventHandler, FileSystemEvent
from watchdog.observers.api import BaseObserver

log = get_logger('WebServer')


@dataclass
class WebServerConfig:
    host: str
    port: int
    root: Path
    cert: Path
    key: Path
    username: str
    password: str


class WebServer(FileSystemEventHandler):
    def __init__(self, observer: BaseObserver, config: WebServerConfig, private_dirs: list[Path]) -> None:
        self._observer = observer
        self._config = config
        self._private_dirs = private_dirs
        self._app = Flask(__name__)
        self._server = create_server(self._app, listen=f'{self._config.host}:{self._config.port}')
        self._wsgi_servers: list[BaseWSGIServer] = []

        if isinstance(self._server, MultiSocketServer):
            self._wsgi_servers = [server for server in self._server.map.values() if isinstance(server, BaseWSGIServer)]
        else:
            self._wsgi_servers = [self._server]

        self._thread = Thread(target=self._start_server)
        self._lock = Lock()

        self._observer.schedule(self, str(self._config.cert.parent), recursive=True)

        @self._app.route('/', defaults={'path': ''})
        @self._app.route('/<path:path>')
        def serve_file_or_directory(path):
            full_path = self._config.root / path

            if any(full_path.is_relative_to(private_dir) for private_dir in self._private_dirs):
                auth = request.authorization
                if not auth or auth.username != config.username or auth.password != config.password:
                    return ('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Private Area"'})

            sort_by = request.args.get('sort', 'name')
            reverse = request.args.get('desc', '0') == '1'

            if full_path.is_dir():
                try:
                    items = sorted(os.listdir(full_path))
                    listing = []

                    if path:
                        parent_path = '/' + quote(str(Path(path).parent))
                        listing.append({
                            'name': '../',
                            'href': parent_path + '/',
                            'is_parent': True,
                            'date': '',
                            'size': '',
                            'sort_key': ''
                        })

                    entries = []

                    for item in items:
                        item_path = os.path.join(full_path, item)
                        is_dir = os.path.isdir(item_path)
                        stat = os.stat(item_path)
                        size = '-' if is_dir else stat.st_size
                        date = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(stat.st_mtime))
                        href = '/' + quote(os.path.join(path, item).replace(os.sep, '/'))
                        if is_dir:
                            href += '/'
                        entries.append({
                            'name': item + ('/' if is_dir else ''),
                            'href': href,
                            'is_parent': False,
                            'is_dir': is_dir,
                            'date': date,
                            'size': '-' if is_dir else f'{size:,} bytes',
                            'sort_key': {
                                'name': item.lower(),
                                'date': date,
                                'size': 0 if is_dir else size
                            }[sort_by]
                        })

                    entries.sort(key=lambda x: x['sort_key'], reverse=reverse)

                    listing.extend(entries)

                    breadcrumbs = []
                    path_accum = ''
                    for part in path.split('/') if path else []:
                        path_accum = os.path.join(path_accum, part)
                        breadcrumbs.append({
                            'name': part,
                            'href': '/' + quote(path_accum.replace(os.sep, '/')) + '/'
                        })

                    return render_template_string(TEMPLATE, items=listing, path=path, breadcrumbs=breadcrumbs,
                                                  sort_by=sort_by, reverse=reverse)
                except PermissionError:
                    abort(403)
            elif os.path.isfile(full_path):
                return send_from_directory(self._config.root, path, as_attachment=False, mimetype='text/plain')
            else:
                abort(404)

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

    def on_date(self, event: FileSystemEvent) -> None:
        if event.src_path == str(self._config.cert):
            with self._lock:
                self._stop_server()
                self._thread = Thread(target=self._start_server)
                self._thread.start()

    def _start_server(self) -> None:
        try:
            log.info('Starting server')
            self._create_ssl_socket()
            self._server.run()
        except Exception as error:
            log.info('Shutdown', reason=error)

    def _stop_server(self) -> None:
        log.info('Stopping server')
        self._server.close()
        self._thread.join(1)

    def _create_ssl_socket(self) -> None:
        for server in self._wsgi_servers:
            ssl_context = SSLContext(PROTOCOL_TLS_SERVER)
            ssl_context.load_cert_chain(certfile=self._config.cert, keyfile=self._config.key)
            server.socket = ssl_context.wrap_socket(server.socket, server_side=True)


TEMPLATE = """
<!doctype html>
<html>
<head>
  <title>Index of /{{ path }}</title>
  <style>
    body { font-family: sans-serif; }
    table { width: 100%; border-collapse: collapse; }
    
    th, td { text-align: left; padding: 4px 8px; }
    th.name, td.name { width: 50%; }
    th.date, td.date { width: 25%; white-space: nowrap; }
    th.size, td.size { width: 25%; text-align: right; white-space: nowrap; }
    tr:nth-child(even) { background-color: #f9f9f9; }
    th { border-bottom: 1px solid #ccc; }
    
    a { text-decoration: none; color: black; }
    a:visited { color: black; }
    a:hover { text-decoration: underline; color: blue; }
  </style>
</head>
<body>
  <h1>Index of /{{ path }}</h1>
  <div class="breadcrumbs">
    <a href="/">root</a>/
    {% for crumb in breadcrumbs %}
      <a href="{{ crumb.href }}">{{ crumb.name }}</a>{% if not loop.last %}/{% endif %}
    {% endfor %}
  </div>
  <table>
    <tr>
      <th onclick="sort('name')">Name {% if sort_by == 'name' %}{{ '↓' if reverse else '↑' }}{% endif %}</th>
      <th onclick="sort('date')">Date {% if sort_by == 'date' %}{{ '↓' if reverse else '↑' }}{% endif %}</th>
      <th onclick="sort('size')">Size {% if sort_by == 'size' %}{{ '↓' if reverse else '↑' }}{% endif %}</th>
    </tr>
    {% for item in items %}
      <tr>
        <td class="name"><a href="{{ item.href }}">{% if item.is_parent %}↩️{% else %}
        {% if item.is_dir %}📁{% else %}📄{% endif %}{% endif %} {{ item.name }}</a></td>
        <td class="date">{{ item.date }}</td>
        <td class="size">{{ item.size }}</td>
      </tr>
    {% endfor %}
  </table>
  <script>
    function sort(by) {
      const url = new URL(window.location.href);
      const current = url.searchParams.get('sort') || 'name';
      const desc = url.searchParams.get('desc') === '1';
      if (current === by) {
        url.searchParams.set('desc', desc ? '0' : '1');
      } else {
        url.searchParams.set('sort', by);
        url.searchParams.set('desc', '0');
      }
      window.location.href = url.toString();
    }
  </script>
</body>
</html>
"""
