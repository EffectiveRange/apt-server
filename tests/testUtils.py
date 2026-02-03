import os
import subprocess
from pathlib import Path

APPLICATION_NAME = 'debian-package-repository'
TEST_RESOURCE_ROOT = Path(os.path.dirname(__file__)).absolute()
REPOSITORY_DIR = Path(TEST_RESOURCE_ROOT).joinpath('test-repo').absolute()
RESOURCE_ROOT = Path(TEST_RESOURCE_ROOT).parent.absolute()
PACKAGE_DIR = TEST_RESOURCE_ROOT / 'test-debs'
RELEASE_TEMPLATE_PATH = RESOURCE_ROOT / 'templates/Release.j2'


def create_test_packages(package_dir: Path, distribution: str, component: str = 'main') -> None:
    create_test_package(package_dir, distribution, component, 'amd64')
    create_test_package(package_dir, distribution, component, 'arm64')


def create_test_package(package_dir: Path, distribution: str, component: str, architecture: str) -> None:
    target_dir = str(package_dir / distribution / component)
    subprocess.call(['/bin/bash', f'{str(TEST_RESOURCE_ROOT)}/package/create_package.sh', target_dir, architecture])
