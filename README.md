# stepmania-to-sqlite

[![PyPI](https://img.shields.io/pypi/v/stepmania-to-sqlite.svg)](https://pypi.org/project/stepmania-to-sqlite/)
[![License](https://img.shields.io/badge/license-Apache%202.0-blue.svg)](https://github.com/rixx/stepmania-to-sqlite/blob/master/LICENSE)

Put stats about your stepmania library into a SQLite database. Will export all songs with data about their groups,
difficulty levels, durations, bpms, etc. Particularly useful if you use the database with
[datasette](https://datasette.readthedocs.io/).

## How to install

    $ pip install stepmania-to-sqlite

Add the `-U` flag to update. Change notes can be found in the ``CHANGELOG`` file, next to this README.

## Importing data

Run the tool with the path to your database - if it doesn't exist yet, it will be created:

    $ stepmania-to-sqlite songs.db

If your library is not located in a directory like ``~/.stepmania*``, you can pass the library path with the -l flag:

    $ stepmania-to-sqlite songs.db -l /path/to/library
    
## Limitations

- Steps are not included, only pre-processed step counts per difficulty.
- Currently, only .sm files are parsed, not the newer .ssc files.

## Thanks

This package is heavily inspired by [github-to-sqlite](https://github.com/dogsheep/github-to-sqlite/) by [Simon
Willison](https://simonwillison.net/2019/Oct/7/dogsheep/).
