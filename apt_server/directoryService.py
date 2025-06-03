# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from context_logger import get_logger
from flask import send_from_directory, render_template_string, abort, request, Response

from apt_server import IWebServer

log = get_logger('DirectoryService')


@dataclass
class DirectoryConfig:
    root_dir: Path
    username: str
    password: str
    private_dirs: list[Path]


class IDirectoryService(object):

    def start(self) -> None:
        raise NotImplementedError()

    def shutdown(self) -> None:
        raise NotImplementedError()


class DirectoryService(IDirectoryService):

    def __init__(self, web_server: IWebServer, config: DirectoryConfig) -> None:
        self._web_server = web_server
        self._config = config

        self._register_routes()

    def _register_routes(self) -> None:
        app = self._web_server.get_app()

        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_file_or_directory(path: str) -> Response:
            full_path = self._config.root_dir / path

            if any(full_path.is_relative_to(private_dir) for private_dir in self._config.private_dirs):
                auth = request.authorization
                if not auth or auth.username != self._config.username or auth.password != self._config.password:
                    return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Private Area"'})

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

                    entries.sort(key=lambda x: x['sort_key'], reverse=reverse)  # type: ignore

                    listing.extend(entries)

                    breadcrumbs = []
                    path_accum = ''
                    for part in path.split('/') if path else []:
                        path_accum = os.path.join(path_accum, part)
                        breadcrumbs.append({
                            'name': part,
                            'href': '/' + quote(path_accum.replace(os.sep, '/')) + '/'
                        })

                    return Response(render_template_string(TEMPLATE, items=listing, path=path, breadcrumbs=breadcrumbs,
                                                           sort_by=sort_by, reverse=reverse))
                except PermissionError:
                    abort(403)
            elif os.path.isfile(full_path):
                return send_from_directory(self._config.root_dir, path, as_attachment=False, mimetype='text/plain')
            else:
                abort(404)

    def start(self) -> None:
        self._web_server.start()

    def shutdown(self) -> None:
        self._web_server.shutdown()


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
