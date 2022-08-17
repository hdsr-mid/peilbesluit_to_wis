import glob
import os
from pathlib import Path


O_drive = Path("O:")

# BASE_DIR avoid 'Path.cwd()', as interactive_map.main() should be callable from everywhere
BASE_DIR = Path(__file__).parent.parent
CONVERTER_DIR = BASE_DIR / "converter"
DATA_DIR = CONVERTER_DIR / "data"
DATA_INPUT_DIR = DATA_DIR / "input"
DATA_OUTPUT_DIR = DATA_DIR / "output"
DATA_EXAMPLE_DIR = DATA_DIR / "example"
LOG_DIR = DATA_OUTPUT_DIR / "log_rotating"
LOG_FILE_PATH = LOG_DIR / "main.log"

PEILMARGE_GIS_EXPORT_DIR = O_drive / "Planvorming\Gebiedsgerichte_plannen\Peilbesluiten\Algemeen\Peilbesluitevaluatie\Product script Inger - peilen, marges en datum"
PEILMARGE_GIS_EXPORT_FILE_PATH = PEILMARGE_GIS_EXPORT_DIR / "Peilbesluitpeilen2019_1107.csv"


def get_last_gis_export_peilmarges_csv() -> Path:
    list_of_files = glob.glob(pathname=PEILMARGE_GIS_EXPORT_DIR / "*.csv")
    assert list_of_files, f"could not find any gis export. We expected at =>1 .csv files in {PEILMARGE_GIS_EXPORT_DIR}"
    latest_file = max(list_of_files, key=os.path.getctime)
    return Path(latest_file)


def check_constants():
    assert CONVERTER_DIR.is_dir()
    assert DATA_DIR.is_dir()
    assert DATA_INPUT_DIR.is_dir()
    assert DATA_OUTPUT_DIR.is_dir()
    assert LOG_DIR.is_dir()


