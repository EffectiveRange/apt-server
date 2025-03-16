# SPDX-FileCopyrightText: 2024 Ferenc Nandor Janky <ferenj@effective-range.com>
# SPDX-FileCopyrightText: 2024 Attila Gombos <attila.gombos@effective-range.com>
# SPDX-License-Identifier: MIT

import os
import shutil
from typing import Optional, Union

from context_logger import get_logger
from gnupg import GPG, ImportResult, Sign, Verify

log = get_logger('AptSigner')


class GpgException(Exception):

    def __init__(self, message: str, result: Union[ImportResult, Sign, Verify]) -> None:
        super().__init__(message)
        self.operation = type(result).__name__.replace('Result', '')
        self.code = result.returncode
        self.status = result.status
        self.error = result.stderr if hasattr(result, 'stderr') else None


class GpgKey(object):

    def __init__(self, key_id: str, key_path: str, passphrase: Optional[str] = None) -> None:
        self.id = key_id
        self.path = key_path
        self.passphrase = passphrase


class AptSigner(object):

    def sign(self) -> None:
        raise NotImplementedError


class ReleaseSigner(AptSigner):

    def __init__(
            self, gpg: GPG, public_key: GpgKey, private_key: GpgKey, repository_dir: str, distributions: set[str]
    ) -> None:
        self._repository_dir = repository_dir
        self._distributions = distributions
        self._public_key = public_key
        self._private_key = private_key
        self._gpg = gpg
        self._initial_run = True

    def sign(self) -> None:
        for distribution in self._distributions:
            dist_path = os.path.abspath(f'{self._repository_dir}/dists/{distribution}')

            if self._initial_run:
                self._add_public_key(dist_path)
                self._import_private_key()

            release_path = f'{dist_path}/Release'

            self._update_release_file(release_path)

            self._clearsign_release_file(dist_path, release_path)

            self._create_detached_signature(release_path)

        self._initial_run = False

    def _update_release_file(self, release_path: str) -> None:
        sign_with = 'SignWith'
        signed_with = f'{sign_with}: {self._private_key.id}'

        with open(release_path, 'r') as release_file:
            lines = release_file.readlines()

        if sign_with in lines[-1]:
            # Update last line
            lines[-1] = signed_with
            with open(release_path, 'w') as release_file:
                release_file.writelines(lines)
        else:
            with open(release_path, 'a') as release_file:
                # Append Release file
                release_file.write(f'\n{signed_with}')

    def _add_public_key(self, dist_path: str) -> None:
        target_path = f'{dist_path}/public.key'
        shutil.copyfile(self._public_key.path, target_path)
        log.info('Added public key file', file=target_path)

    def _import_private_key(self) -> None:
        key_id = self._private_key.id
        key_path = self._private_key.path

        if self._is_key_available():
            log.debug('Private key already present', key_id=key_id)
        else:
            log.info('Importing private key', key_id=key_id)

            result: ImportResult = self._gpg.import_keys_file(key_path)

            if result.returncode != 0:
                log.error('Failed to import private key', file=key_path, key_id=key_id)
                raise GpgException('Failed to import private key', result)
            else:
                log.debug('Imported private key', key_id=key_id)

    def _is_key_available(self) -> bool:
        for key in self._gpg.list_keys():
            if key['fingerprint'] == self._private_key.id:
                return True

        return False

    def _clearsign_release_file(self, dist_path: str, release_path: str) -> None:
        in_release_path = f'{dist_path}/InRelease'

        self._create_signature(release_path, in_release_path, detach=False)

        log.info('Created signed Release file', file=in_release_path)

    def _create_detached_signature(self, release_path: str) -> None:
        signature_path = f'{release_path}.gpg'

        self._create_signature(release_path, signature_path, detach=True)

        log.info('Created signature file', file=signature_path)

    def _create_signature(self, release_path: str, signature_path: str, detach: bool) -> None:
        result: Sign = self._gpg.sign_file(
            release_path,
            keyid=self._private_key.id,
            passphrase=self._private_key.passphrase,
            output=signature_path,
            detach=detach,
        )

        if result.returncode != 0:
            log.error('Failed to create signature', file=release_path, signature=signature_path)
            raise GpgException('Failed to create signature', result)
        else:
            log.debug('Created signature', file=signature_path)

        self._verify_signature(release_path, signature_path, detached=detach)

    def _verify_signature(self, release_path: str, signature_path: str, detached: bool) -> None:
        with open(signature_path, 'rb') as signature_file:
            result: Verify = self._gpg.verify_file(signature_file, release_path if detached else None)

        if result.returncode != 0:
            log.error('Failed to verify signature', file=release_path, signature=signature_path)
            raise GpgException('Failed to verify signature', result)
        else:
            log.debug('Verified signature', file=signature_path)
