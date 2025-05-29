import os
import subprocess
from pathlib import Path

TEST_RESOURCE_ROOT = str(Path(os.path.dirname(__file__)).absolute())
REPOSITORY_DIR = Path(TEST_RESOURCE_ROOT).joinpath('test-repo').absolute()
RESOURCE_ROOT = str(Path(TEST_RESOURCE_ROOT).parent.absolute())


def create_test_packages(package_dir: Path, distribution: str) -> None:
    create_test_package(package_dir, distribution, 'amd64')
    create_test_package(package_dir, distribution, 'arm64')


def create_test_package(package_dir: Path, distribution: str, architecture: str) -> None:
    target_dir = f'{package_dir}/{distribution}'
    subprocess.call(['/bin/bash', f'{TEST_RESOURCE_ROOT}/package/create_package.sh', target_dir, architecture])
