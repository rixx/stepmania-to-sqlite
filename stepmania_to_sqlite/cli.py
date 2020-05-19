import click
import sqlite_utils

from stepmania_to_sqlite import utils


@click.command()
@click.argument(
    "db_path",
    type=click.Path(file_okay=True, dir_okay=False, allow_dash=False),
    required=True,
)
@click.option(
    "-l",
    "--location",
    type=click.Path(file_okay=False, dir_okay=True, allow_dash=False),
    default=None,
    help="Path to stepmania location, defaults to looking at ~/.stepmania*",
)
def update(db_path, location):
    db = sqlite_utils.Database(db_path)
    utils.get_songs(db, changed_only=True, save=True)


update()
