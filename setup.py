from setuptools import setup

setup(
    name='apt-server',
    version='1.1.4',
    description='APT server with dynamic package pool handling',
    author='Ferenc Nandor Janky & Attila Gombos',
    author_email='info@effective-range.com',
    packages=['apt_server', 'apt_repository'],
    scripts=['bin/apt-server.py'],
    data_files=[('templates', ['templates/Release.template'])],
    install_requires=['watchdog', 'jinja2', 'python-gnupg', 'requests',
                      'python-context-logger@git+https://github.com/EffectiveRange/python-context-logger.git@latest']
)
