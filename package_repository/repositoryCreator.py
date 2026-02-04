# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import gzip
import hashlib
import os
import shutil
import subprocess
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Tuple

from common_utility import create_directory, render_template_file
from context_logger import get_logger

from package_repository import RepositoryCache

log = get_logger('RepositoryCreator')


@dataclass
class RepositoryConfig:
    application_name: str
    application_version: str
    distributions: set[str]
    components: set[str]
    architectures: set[str]
    repository_dir: Path
    deb_package_dir: Path
    release_template: Path


class RepositoryCreator:

    def initialize(self) -> None:
        raise NotImplementedError()

    def create(self, distribution: str) -> None:
        raise NotImplementedError()


class DefaultRepositoryCreator(RepositoryCreator):

    def __init__(self, cache: RepositoryCache, config: RepositoryConfig) -> None:
        self._cache = cache
        self._config = config
        self._architectures = sorted({'all'} | config.architectures)

    def initialize(self) -> None:
        self._create_repository_dir()
        self._link_package_dir()

    def create(self, distribution: str) -> None:
        current_dir = os.getcwd()

        os.chdir(self._config.repository_dir)

        packages_files = self._generate_packages_files(distribution)

        self._generate_release_file(distribution, packages_files)

        os.chdir(current_dir)

    def _create_repository_dir(self) -> None:
        if not self._config.repository_dir.is_dir():
            log.info('Creating repository directory', directory=str(self._config.repository_dir))
            os.makedirs(self._config.repository_dir)

    def _link_package_dir(self) -> None:
        target_link = self._config.repository_dir / 'pool'

        if target_link.exists() or target_link.is_symlink():
            log.info('Removing existing link', target=str(target_link))
            self._clean_target(target_link)

        source_dir = self._config.deb_package_dir

        if not source_dir.is_dir():
            log.info('Creating .deb package directory', directory=str(source_dir))
            os.makedirs(source_dir)

        os.symlink(source_dir, target_link, target_is_directory=True)

        log.info('Linked .deb package directory', source=str(source_dir), target=str(target_link))

    def _clean_target(self, target_link: Path) -> None:
        if target_link.is_symlink():
            target_link.unlink()
        elif target_link.is_dir():
            shutil.rmtree(target_link)
        else:
            os.remove(target_link)

    def _generate_packages_files(self, distribution: str) -> list[Path]:
        packages_files = []

        for component in self._config.components:
            target_dir = self._config.repository_dir / 'dists' / distribution / component

            create_directory(target_dir)

            package_dir = Path('pool') / distribution / component

            create_directory(package_dir)

            for architecture in self._architectures:
                arch_dir = target_dir / f'binary-{architecture}'

                create_directory(arch_dir)

                command = ['dpkg-scanpackages', '--multiversion', '--arch', architecture, str(package_dir)]
                result = subprocess.run(command, capture_output=True, check=True)

                packages_content = result.stdout

                packages_path = arch_dir / 'Packages'

                self._create_file(distribution, packages_path, packages_content)

                log.info('Generated Packages file', file=str(packages_path),
                         distribution=distribution, component=component, architecture=architecture)

                packages_files.append(packages_path)

                compressed_path = Path(f'{packages_path}.gz')

                self._create_file(distribution, compressed_path, packages_content, compressed=True)

                packages_files.append(compressed_path)

        return packages_files

    def _generate_release_file(self, distribution: str, packages_files: list[Path]) -> None:
        dist_path = self._config.repository_dir / 'dists' / distribution

        md5_checksums = []
        sha1_checksums = []
        sha256_checksums = []

        for packages_file in packages_files:
            md5, sha1, sha256 = self._generate_checksums(packages_file)
            file_size = os.stat(packages_file).st_size
            file_path = str(packages_file)[len(str(dist_path)) + 1:]
            md5_checksums.append(f' {md5} {file_size} {file_path}')
            sha1_checksums.append(f' {sha1} {file_size} {file_path}')
            sha256_checksums.append(f' {sha256} {file_size} {file_path}')

        context = {
            'origin': self._config.application_name,
            'label': self._config.application_name,
            'version': self._config.application_version,
            'codename': distribution,
            'date': datetime.now(timezone.utc).strftime("%a, %d %b %Y %H:%M:%S UTC"),
            'architectures': ' '.join(self._architectures),
            'components': ' '.join(self._config.components),
            'md5_checksums': '\n'.join(md5_checksums),
            'sha1_checksums': '\n'.join(sha1_checksums),
            'sha256_checksums': '\n'.join(sha256_checksums),
        }

        rendered_content = render_template_file(self._config.release_template, context).encode('utf-8')

        release_path = dist_path / 'Release'

        self._create_file(distribution, release_path, rendered_content)

        log.info('Generated Release file', file=str(release_path), distribution=distribution)

    def _create_file(self, distribution: str, file_path: Path, content: bytes, compressed: bool = False) -> None:
        self._cache.store(distribution, file_path, content)

        with (gzip.open(file_path, 'wb') if compressed else open(file_path, 'wb')) as file:
            file.write(content)

    def _generate_checksums(self, file_path: Path) -> Tuple[str, str, str]:
        md5_hashes = hashlib.md5()
        sha1_hashes = hashlib.sha1()
        sha256_hashes = hashlib.sha256()

        with open(file_path, 'rb') as f:
            data = f.read()
            md5_hashes.update(data)
            sha1_hashes.update(data)
            sha256_hashes.update(data)

        return md5_hashes.hexdigest(), sha1_hashes.hexdigest(), sha256_hashes.hexdigest()
