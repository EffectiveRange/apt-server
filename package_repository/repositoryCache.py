# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

from pathlib import Path
from threading import Lock

from context_logger import get_logger

log = get_logger('RepositoryCache')


class RepositoryCache:

    def lock(self, distribution: str) -> None:
        raise NotImplementedError()

    def unlock(self, distribution: str) -> None:
        raise NotImplementedError()

    def store(self, distribution: str, path: Path, content: bytes) -> None:
        raise NotImplementedError()

    def load(self, distribution: str, path: Path) -> bytes | None:
        raise NotImplementedError()

    def clear(self, distribution: str) -> None:
        raise NotImplementedError()


class DefaultRepositoryCache(RepositoryCache):

    def __init__(self) -> None:
        self._distribution_locks: dict[str, Lock] = {}
        self._distribution_cache: dict[str, dict[Path, bytes]] = {}

    def lock(self, distribution: str) -> None:
        log.debug('Locking cache for distribution', distribution=distribution)
        self._get_lock(distribution).acquire()

    def unlock(self, distribution: str) -> None:
        log.debug('Unlocking cache for distribution', distribution=distribution)
        lock = self._get_lock(distribution)
        if lock.locked():
            lock.release()

    def store(self, distribution: str, path: Path, content: bytes) -> None:
        with self._get_lock(distribution):
            self._store(distribution, path, content)

    def load(self, distribution: str, path: Path) -> bytes | None:
        with self._get_lock(distribution):
            content = self._distribution_cache.get(distribution, {}).get(path)

            if not content:
                log.debug('File not found in cache, loading from file system', path=str(path))

                if path.is_file():
                    try:
                        with open(path, 'rb') as file:
                            content = file.read()
                    except Exception as error:
                        log.error('Failed to read file from file system', path=str(path), error=str(error))
                        return None

                    self._store(distribution, path, content)
                else:
                    log.debug('File does not exist on file system', path=str(path))
                    return None

            return content

    def clear(self, distribution: str) -> None:
        log.debug('Clearing cache for distribution', distribution=distribution)

        if distribution in self._distribution_cache:
            self._distribution_cache[distribution] = {}

        self.unlock(distribution)

    def _get_lock(self, distribution: str) -> Lock:
        if distribution not in self._distribution_locks:
            self._distribution_locks[distribution] = Lock()

        return self._distribution_locks[distribution]

    def _store(self, distribution: str, path: Path, content: bytes) -> None:
        if distribution not in self._distribution_cache:
            self._distribution_cache[distribution] = {}

        log.debug('Storing content in cache', distribution=distribution, path=str(path))
        self._distribution_cache[distribution][path] = content
