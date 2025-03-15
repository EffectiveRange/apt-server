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
from typing import Tuple

from context_logger import get_logger
from jinja2 import Environment, FileSystemLoader

log = get_logger('AptRepository')


class AptRepository(object):

    def create(self) -> None:
        raise NotImplementedError


class LinkedPoolAptRepository(AptRepository):

    def __init__(
        self,
        application_name: str,
        architectures: set[str],
        distributions: set[str],
        repository_dir: str,
        deb_package_dir: str,
        template_path: str,
    ) -> None:
        self._application_name = application_name
        self._architectures = sorted({'all'} | architectures)
        self._distributions = distributions if distributions else ['stable']
        self._repository_dir = repository_dir
        self._deb_package_dir = os.path.abspath(deb_package_dir)
        self._template_path = os.path.abspath(template_path)
        self._initial_run = True

    def create(self) -> None:
        if self._initial_run:
            pool_dir = self._create_pool_dir()
            self._link_package_dir(pool_dir)
            self._initial_run = False

        packages_files = self._generate_packages_files()

        self._generate_release_file(packages_files)

    def _create_pool_dir(self) -> str:
        pool_dir = f'{self._repository_dir}/pool'

        if not os.path.isdir(pool_dir):
            log.info('Creating pool directory', directory=pool_dir)
            os.makedirs(pool_dir)

        return pool_dir

    def _link_package_dir(self, pool_dir: str) -> None:
        target_link = os.path.abspath(f'{pool_dir}/main')

        if os.path.exists(target_link) or os.path.islink(target_link):
            log.info('Removing existing link', target=target_link)
            self._clean_target(target_link)

        source_dir = self._deb_package_dir

        if not os.path.isdir(source_dir):
            log.info('Creating .deb package directory', directory=source_dir)
            os.makedirs(source_dir)

        os.symlink(source_dir, target_link, target_is_directory=True)

        log.info('Linked .deb package directory', source=source_dir, target=target_link)

    def _clean_target(self, target_link: str) -> None:
        if os.path.islink(target_link):
            os.unlink(target_link)
        elif os.path.isdir(target_link):
            shutil.rmtree(target_link)
        else:
            os.remove(target_link)

    def _generate_packages_files(self) -> list[str]:
        packages_files = []

        current_dir = os.getcwd()

        os.chdir(self._repository_dir)

        for distribution in self._distributions:
            target_dir = os.path.abspath(f'{self._repository_dir}/dists/{distribution}/main')

            for arch in self._architectures:
                arch_dir = f'{target_dir}/binary-{arch}'

                if not os.path.isdir(arch_dir):
                    os.makedirs(arch_dir)

                packages_file = f'{arch_dir}/Packages'

                with open(packages_file, 'w') as f:
                    subprocess.call(['dpkg-scanpackages', '--arch', arch, f'pool/main/{distribution}/'], stdout=f)

                packages_files.append(packages_file)

                log.info('Generated Packages file', distribution=distribution, architecture=arch, file=packages_file)

                compressed_file = f'{packages_file}.gz'

                with open(packages_file, 'rb') as f_in, gzip.open(compressed_file, 'wb') as f_out:
                    f_out.writelines(f_in)

                packages_files.append(compressed_file)

        os.chdir(current_dir)

        return packages_files

    def _generate_release_file(self, packages_files: list[str]) -> None:
        for distribution in self._distributions:
            dist_path = os.path.abspath(f'{self._repository_dir}/dists/{distribution}')

            md5_checksums = []
            sha1_checksums = []
            sha256_checksums = []

            for packages_file in packages_files:
                md5, sha1, sha256 = self._generate_checksums(packages_file)
                file_size = os.stat(packages_file).st_size
                file_path = packages_file[len(dist_path) + 1 :]
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

            rendered_content = self._render_release_template(self._template_path, context)

            release_path = f'{dist_path}/Release'

            with open(release_path, 'w') as release_file:
                release_file.write(rendered_content)

            log.info('Generated Release file', distribution=distribution, file=release_path)

    def _get_version(self) -> str:
        try:
            return version(self._application_name)
        except PackageNotFoundError:
            return 'none'

    def _generate_checksums(self, file_path: str) -> Tuple[str, str, str]:
        md5_hashes = hashlib.md5()
        sha1_hashes = hashlib.sha1()
        sha256_hashes = hashlib.sha256()

        with open(file_path, 'rb') as f:
            data = f.read()
            md5_hashes.update(data)
            sha1_hashes.update(data)
            sha256_hashes.update(data)

        return md5_hashes.hexdigest(), sha1_hashes.hexdigest(), sha256_hashes.hexdigest()

    def _render_release_template(self, template_path: str, context: dict[str, str]) -> str:
        env = Environment(loader=FileSystemLoader(os.path.dirname(template_path)))
        template = env.get_template(os.path.basename(template_path))
        return template.render(context)
