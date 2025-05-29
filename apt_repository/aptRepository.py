# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import gzip
import hashlib
import os
import shutil
import subprocess
from datetime import datetime
from importlib.metadata import PackageNotFoundError, version
from pathlib import Path
from typing import Tuple

from common_utility import create_directory, render_template_file
from context_logger import get_logger

log = get_logger('AptRepository')


class AptRepository(object):

    def create(self) -> None:
        raise NotImplementedError


class LinkedPoolAptRepository(AptRepository):

    def __init__(self, application_name: str, architectures: set[str], distributions: set[str], repository_dir: Path,
                 deb_package_dir: Path, release_template: Path) -> None:
        self._application_name = application_name
        self._architectures = sorted({'all'} | architectures)
        self._distributions = distributions
        self._repository_dir = repository_dir
        self._deb_package_dir = deb_package_dir
        self._release_template = release_template
        self._initial_run = True

    def create(self) -> None:
        if self._initial_run:
            pool_dir = self._create_pool_dir()
            self._link_package_dir(pool_dir)
            self._initial_run = False

        current_dir = os.getcwd()

        os.chdir(self._repository_dir)

        for distribution in self._distributions:
            packages_files = self._generate_packages_files(distribution)

            self._generate_release_file(distribution, packages_files)

        os.chdir(current_dir)

    def _create_pool_dir(self) -> Path:
        pool_dir = self._repository_dir / 'pool'

        if not pool_dir.is_dir():
            log.info('Creating pool directory', directory=str(pool_dir))
            os.makedirs(pool_dir)

        return pool_dir

    def _link_package_dir(self, pool_dir: Path) -> None:
        target_link = pool_dir / 'main'

        if target_link.exists() or target_link.is_symlink():
            log.info('Removing existing link', target=str(target_link))
            self._clean_target(target_link)

        source_dir = self._deb_package_dir

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

        target_dir = self._repository_dir / f'dists/{distribution}/main'

        create_directory(target_dir)

        package_dir = Path(f'pool/main/{distribution}')

        create_directory(package_dir)

        for arch in self._architectures:
            arch_dir = target_dir / f'binary-{arch}'

            create_directory(arch_dir)

            packages_file = arch_dir / 'Packages'

            with open(packages_file, 'w') as file:
                subprocess.call(['dpkg-scanpackages', '--multiversion', '--arch', arch, package_dir], stdout=file)

            packages_files.append(packages_file)

            log.info('Generated Packages file', distribution=distribution, architecture=arch, file=str(packages_file))

            compressed_file = Path(f'{packages_file}.gz')

            with open(packages_file, 'rb') as file_in, gzip.open(compressed_file, 'wb') as file_out:
                file_out.writelines(file_in)

            packages_files.append(compressed_file)

        return packages_files

    def _generate_release_file(self, distribution: str, packages_files: list[Path]) -> None:
        dist_path = f'{self._repository_dir}/dists/{distribution}'

        md5_checksums = []
        sha1_checksums = []
        sha256_checksums = []

        for packages_file in packages_files:
            md5, sha1, sha256 = self._generate_checksums(packages_file)
            file_size = os.stat(packages_file).st_size
            file_path = str(packages_file)[len(dist_path) + 1:]
            md5_checksums.append(f' {md5} {file_size} {file_path}')
            sha1_checksums.append(f' {sha1} {file_size} {file_path}')
            sha256_checksums.append(f' {sha256} {file_size} {file_path}')

        context = {
            'origin': self._application_name,
            'label': self._application_name,
            'codename': distribution,
            'version': self._get_version(),
            'architectures': ' '.join(self._architectures),
            'date': datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S UTC"),
            'md5_checksums': '\n'.join(md5_checksums),
            'sha1_checksums': '\n'.join(sha1_checksums),
            'sha256_checksums': '\n'.join(sha256_checksums),
        }

        rendered_content = render_template_file(self._release_template, context)

        release_path = f'{dist_path}/Release'

        with open(release_path, 'w') as release_file:
            release_file.write(rendered_content)

        log.info('Generated Release file', distribution=distribution, file=str(release_path))

    def _get_version(self) -> str:
        try:
            return version(self._application_name)
        except PackageNotFoundError:
            return 'none'

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
