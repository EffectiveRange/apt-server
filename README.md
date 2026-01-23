# Repository Coverage

[Full report](https://htmlpreview.github.io/?https://github.com/EffectiveRange/apt-server/blob/python-coverage-comment-action-data/htmlcov/index.html)

| Name                             |    Stmts |     Miss |   Branch |   BrPart |   Cover |   Missing |
|--------------------------------- | -------: | -------: | -------: | -------: | ------: | --------: |
| apt\_repository/\_\_init\_\_.py  |        2 |        0 |        0 |        0 |    100% |           |
| apt\_repository/aptRepository.py |      109 |        5 |       18 |        2 |     93% |40->45, 85-88, 163-164 |
| apt\_repository/aptSigner.py     |       99 |        0 |       18 |        0 |    100% |           |
| apt\_server/\_\_init\_\_.py      |        3 |        0 |        0 |        0 |    100% |           |
| apt\_server/aptServer.py         |       68 |        0 |        6 |        0 |    100% |           |
| apt\_server/directoryService.py  |       82 |        0 |       18 |        0 |    100% |           |
| apt\_server/webServer.py         |       52 |        3 |        4 |        2 |     91% |60, 70->exit, 85-86 |
| **TOTAL**                        |  **415** |    **8** |   **64** |    **4** | **97%** |           |


## Setup coverage badge

Below are examples of the badges you can use in your main branch `README` file.

### Direct image

[![Coverage badge](https://raw.githubusercontent.com/EffectiveRange/apt-server/python-coverage-comment-action-data/badge.svg)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/apt-server/blob/python-coverage-comment-action-data/htmlcov/index.html)

This is the one to use if your repository is private or if you don't want to customize anything.

### [Shields.io](https://shields.io) Json Endpoint

[![Coverage badge](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/EffectiveRange/apt-server/python-coverage-comment-action-data/endpoint.json)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/apt-server/blob/python-coverage-comment-action-data/htmlcov/index.html)

Using this one will allow you to [customize](https://shields.io/endpoint) the look of your badge.
It won't work with private repositories. It won't be refreshed more than once per five minutes.

### [Shields.io](https://shields.io) Dynamic Badge

[![Coverage badge](https://img.shields.io/badge/dynamic/json?color=brightgreen&label=coverage&query=%24.message&url=https%3A%2F%2Fraw.githubusercontent.com%2FEffectiveRange%2Fapt-server%2Fpython-coverage-comment-action-data%2Fendpoint.json)](https://htmlpreview.github.io/?https://github.com/EffectiveRange/apt-server/blob/python-coverage-comment-action-data/htmlcov/index.html)

This one will always be the same color. It won't work for private repos. I'm not even sure why we included it.

## What is that?

This branch is part of the
[python-coverage-comment-action](https://github.com/marketplace/actions/python-coverage-comment)
GitHub Action. All the files in this branch are automatically generated and may be
overwritten at any moment.