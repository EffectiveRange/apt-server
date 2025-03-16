import os
import subprocess
from difflib import Differ
from pathlib import Path

TEST_RESOURCE_ROOT = str(Path(os.path.dirname(__file__)).absolute())
REPOSITORY_DIR = str(Path(TEST_RESOURCE_ROOT).joinpath('test-repo').absolute())
RESOURCE_ROOT = str(Path(TEST_RESOURCE_ROOT).parent.absolute())


def create_test_packages(package_dir: str, distribution: str) -> None:
    create_test_package(package_dir, distribution, 'amd64')
    create_test_package(package_dir, distribution, 'arm64')


def create_test_package(package_dir: str, distribution: str, architecture: str) -> None:
    target_dir = f'{package_dir}/{distribution}'
    subprocess.call(['/bin/bash', f'{TEST_RESOURCE_ROOT}/package/create_package.sh', target_dir, architecture])


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
