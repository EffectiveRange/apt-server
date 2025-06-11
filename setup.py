from setuptools import setup, find_packages

setup(
    name='apt-server',
    description='APT server with dynamic package pool handling',
    author='Ferenc Nandor Janky & Attila Gombos',
    author_email='info@effective-range.com',
    packages=find_packages(exclude=['tests']),
    scripts=['bin/apt-server.py'],
    data_files=[('config', ['config/apt-server.conf']), ('templates', ['templates/Release.j2'])],
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
