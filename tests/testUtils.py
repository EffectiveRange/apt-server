import os
import shutil
import subprocess
import time
from difflib import Differ
from pathlib import Path
from typing import Callable, Any

TEST_RESOURCE_ROOT = str(Path(os.path.dirname(__file__)).absolute())
REPOSITORY_DIR = str(Path(TEST_RESOURCE_ROOT).joinpath('test-repo').absolute())
RESOURCE_ROOT = str(Path(TEST_RESOURCE_ROOT).parent.absolute())


def delete_directory(directory: str) -> None:
    if os.path.isdir(directory):
        shutil.rmtree(directory)


def create_directory(directory: str) -> None:
    if not os.path.isdir(directory):
        os.makedirs(directory, exist_ok=True)


def create_file(file: str, content: str) -> None:
    create_directory(os.path.dirname(file))
    with open(file, 'w') as f:
        f.write(content)


def create_test_packages(package_dir: str) -> None:
    create_test_package(package_dir, 'amd64')
    create_test_package(package_dir, 'arm64')


def create_test_package(package_dir: str, architecture: str) -> None:
    subprocess.call(['/bin/bash', f'{TEST_RESOURCE_ROOT}/package/create_package.sh', package_dir, architecture])


def fill_template(template_file: str, context: dict) -> str:
    with open(template_file, 'r') as f:
        template = f.read()

    for key, value in context.items():
        template = template.replace(f'{{{{{key}}}}}', value)

    return template


def compare_files(file1, file2, exclusions):
    with open(file1, 'r') as f1, open(file2, 'r') as f2:
        lines1 = f1.readlines()
        lines2 = f2.readlines()

    return compare_lines(lines1, lines2, exclusions)


def compare_lines(lines1, lines2, exclusions):
    all_lines_match = True

    for line in Differ().compare(lines1, lines2):
        line = line.strip()
        if not any(keyword in line for keyword in exclusions):
            if not line.startswith('?'):
                print(line)
            if line.startswith(('-', '+')):
                all_lines_match = False
        elif line.startswith('+'):
            print(line.replace('+ ', ''))

    return all_lines_match


def wait_for_condition(timeout: float, condition: Callable[..., bool], *args: Any, **kwargs: Any) -> None:
    time_step = 0.01
    total_time = 0.0

    while total_time <= timeout:
        if args or kwargs:
            if condition(*args, **kwargs):
                return
        else:
            if condition():
                return
        total_time += time_step
        time.sleep(time_step)
    else:
        raise TimeoutError(f'Failed to meet condition in {timeout} seconds')
