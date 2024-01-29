from converter.constants import PEILMARGE_GIS_EXPORT_DIR
from pathlib import Path

import glob
import logging
import numpy as np  # noqa numpy comes with geopandas
import os
import pandas as pd  # noqa pandas comes with geopandas


logger = logging.getLogger(__name__)


def get_progress(iteration_nr: int, nr_to_do: int):
    progress_percentage = int((100 * iteration_nr) / nr_to_do)
    return progress_percentage


def get_last_gis_export_peilmarges_csv() -> Path:
    list_of_files = glob.glob(pathname=(PEILMARGE_GIS_EXPORT_DIR / "*.csv").as_posix())  # noqa
    assert list_of_files, f"could not find any gis export. We expected at =>1 .csv files in {PEILMARGE_GIS_EXPORT_DIR}"
    latest_file = max(list_of_files, key=os.path.getctime)
    latest_file_path = Path(latest_file)
    assert latest_file_path.is_file()
    return latest_file_path
