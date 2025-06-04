# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import os
import time
from dataclasses import dataclass
from pathlib import Path
from urllib.parse import quote

from context_logger import get_logger
from flask import send_from_directory, abort, request, Response, render_template

from apt_server import IWebServer

log = get_logger('DirectoryService')


@dataclass
class DirectoryConfig:
    root_dir: Path
    username: str
    password: str
    private_dirs: list[Path]
    html_template: Path


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

    def start(self) -> None:
        self._web_server.start()

    def shutdown(self) -> None:
        self._web_server.shutdown()

    def _register_routes(self) -> None:
        app = self._web_server.get_app()

        app.template_folder = str(self._config.html_template.parent)

        @app.route('/', defaults={'path': ''})
        @app.route('/<path:path>')
        def serve_file_or_directory(path: str) -> Response:
            full_path = self._config.root_dir / path

            if not self._authorize(full_path):
                return Response('Unauthorized', 401, {'WWW-Authenticate': 'Basic realm="Private Area"'})

            if full_path.is_dir():
                try:
                    return self._list_directory(path, full_path)
                except PermissionError:
                    abort(403)
            elif os.path.isfile(full_path):
                return send_from_directory(self._config.root_dir, path, as_attachment=False, mimetype='text/plain')
            else:
                abort(404)

    def _authorize(self, full_path: Path) -> bool:
        if any(full_path.is_relative_to(private_dir) for private_dir in self._config.private_dirs):
            auth = request.authorization
            if not auth or auth.username != self._config.username or auth.password != self._config.password:
                return False

        return True

    def _list_directory(self, path: str, full_path: Path) -> Response:
        sort_by = request.args.get('sort', 'name')
        reverse = request.args.get('desc', '0') == '1'

        listing = []

        if path:
            listing.append(self._create_parent_entry(path))

        entries = []

        for item in sorted(os.listdir(full_path)):
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

        return Response(render_template('directory.j2', items=listing, path=path, breadcrumbs=breadcrumbs,
                                        sort_by=sort_by, reverse=reverse))

    def _create_parent_entry(self, path: str) -> dict:
        parent_path = '/' + quote(str(Path(path).parent))
        return {
            'name': '../',
            'href': parent_path + '/',
            'is_parent': True,
            'date': '',
            'size': '',
            'sort_key': ''
        }
