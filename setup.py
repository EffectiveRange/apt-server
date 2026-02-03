from setuptools import setup, find_packages

setup(
    name='debian-package-repository',
    description='Debian package repository server to serve .deb packages over HTTP',
    author='Ferenc Nandor Janky & Attila Gombos',
    author_email='info@effective-range.com',
    packages=find_packages(exclude=['tests']),
    scripts=['bin/debian-package-repository.py'],
    data_files=[
        ('config', ['config/debian-package-repository.conf']),
        ('templates', ['templates/Release.j2', 'templates/directory.j2'])
    ],
    use_scm_version=True,
    setup_requires=["setuptools_scm"],
    install_requires=[
        'flask',
        'waitress',
        'watchdog',
        'jinja2',
        'python-gnupg',
        'requests',
        'python-context-logger@git+https://github.com/EffectiveRange/python-context-logger.git@latest',
        'python-common-utility@git+https://github.com/EffectiveRange/python-common-utility.git@latest',
    ],
)
