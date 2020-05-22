"""car detection.scripts.cli."""


import click
import sys
sys.path.append("..")
from car_detection.encoding.inference import car_detection_process


@click.group(short_help="COGEO detection")
@click.version_option(version="1.0.0", message="%(version)s")
def detection():
    """Rasterio car_detection subcommands."""
    pass


@detection.command(short_help="Use AI Model to Detect Cars.")
@click.option(
    "--cat_ids",
    "--c",
    multiple=False,
    type=str,
    help="catalog id list for predict",
)
@click.option(
    "--paths",
    "--p",
    multiple=False,
    type=str,
    help="obs path list for predict",
)
@click.option(
    "--aoi",
    "--a",
    multiple=False,
    type=str,
    help="aio for predict",
)
@click.option(
    "--output_path",
    "--o",
    multiple=False,
    type=str,
    help="the output path for result",
)
def detection(cat_ids, paths, aoi, output_path):
    """Use AI Model to Detect Cars."""
    car_detection_process(cat_ids=cat_ids, paths=paths, aoi=aoi, output_path=output_path)
