from enum import Enum
from pathlib import Path

import glob
import os


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

PEILMARGE_GIS_EXPORT_DIR = (
    O_drive
    / "Planvorming\Gebiedsgerichte_plannen\Peilbesluiten\Algemeen\Peilbesluitevaluatie\Product script Inger - peilen, marges en datum"  # noqa
)
PEILMARGE_GIS_EXPORT_FILE_PATH = PEILMARGE_GIS_EXPORT_DIR / "Peilbesluitpeilen2019_1107.csv"

CREATE_CSV_WITH_ERRORS = True
CREATE_XML = True
RAISE_ON_CSV_WARNING_ROW = False
RAISE_ON_CSV_ERROR_ROW = False

MIN_ALLOWED_MNAP = -10
MAX_ALLOWED_MNAP = 10

MIN_ALLOW_LOWER_MARGIN_CM = 0
MAX_ALLOW_LOWER_MARGIN_CM = 100 * 10  # yes... 10 meters

MIN_ALLOW_UPPER_MARGIN_CM = 0
MAX_ALLOW_UPPER_MARGIN_CM = 100 * 10  # yes... 10 meters

TAB = "    "


def get_last_gis_export_peilmarges_csv() -> Path:
    list_of_files = glob.glob(pathname=(PEILMARGE_GIS_EXPORT_DIR / "*.csv").as_posix())  # noqa
    assert list_of_files, f"could not find any gis export. We expected at =>1 .csv files in {PEILMARGE_GIS_EXPORT_DIR}"
    latest_file = max(list_of_files, key=os.path.getctime)
    latest_file_path = Path(latest_file)
    assert latest_file_path.is_file()
    return latest_file_path


def check_constants():
    assert CONVERTER_DIR.is_dir()
    assert DATA_DIR.is_dir()
    assert DATA_INPUT_DIR.is_dir()
    assert DATA_OUTPUT_DIR.is_dir()
    assert LOG_DIR.is_dir()


class DateFormats(Enum):
    yyyymmdd = "%Y%m%d"  # 20001231
    dd_mm = "%d-%m"  # 31-12
    yyyy_dd_mm = "%Y-%d-%m"  # 2000-31-12
    yyyy_mm_dd = "%Y-%m-%d"  # 2000-12-31


class TimestampColumns:
    eind_winter = "eind_winter"
    begin_zomer = "begin_zomer"
    eind_zomer = "eind_winter"
    begin_winter = "begin_winter"


class TimeSeriesMetaBase:
    @property
    def longname(self) -> str:
        raise NotImplementedError

    @property
    def parameter_id(self) -> str:
        raise NotImplementedError

    @property
    def source_system(self) -> str:
        return "tijdreeks FEWS-PI.xls"

    @property
    def units(self) -> str:
        raise NotImplementedError

    @property
    def timestamp_columns(self) -> list:
        raise NotImplementedError


class Peilbesluitpeil(TimeSeriesMetaBase):
    longname = "Peilbesluitpeil"
    units = "m"  # TODO: @roger/job: peil is to mnap en geen m (in voorbeeld xml staat m)
    parameter_id = "Hpl"
    timestamp_columns = [
        TimestampColumns.eind_winter,
        TimestampColumns.begin_zomer,
        TimestampColumns.eind_zomer,
        TimestampColumns.begin_winter,
    ]


class TweedeOndergrens(TimeSeriesMetaBase):
    longname = " Peilbesluitpeil tweede ondergrens"
    units = "m"  # TODO: @roger/job: peil is to mnap en geen m (in voorbeeld xml staat m)
    parameter_id = "Hpl.2o.0"
    timestamp_columns = [
        TimestampColumns.eind_winter,
        TimestampColumns.begin_zomer,
        TimestampColumns.eind_zomer,
        TimestampColumns.begin_winter,
    ]


class EersteOndergrens(TimeSeriesMetaBase):
    longname = " Peilbesluitpeil eerste ondergrens"
    units = "m"  # TODO: @roger/job: peil is to mnap en geen m (in voorbeeld xml staat m)
    parameter_id = "Hpl.o.0"
    timestamp_columns = [
        TimestampColumns.begin_zomer,
        TimestampColumns.eind_zomer,
    ]


class TweedeBovengrens(TimeSeriesMetaBase):
    longname = " Peilbesluitpeil tweede ondergrens"
    units = "m"  # TODO: @roger/job: peil is to mnap en geen m (in voorbeeld xml staat m)
    parameter_id = "Hpl.b.0"
    timestamp_columns = [
        TimestampColumns.eind_winter,
        TimestampColumns.begin_winter,
    ]


class EersteBovengrens(TimeSeriesMetaBase):
    longname = " Peilbesluitpeil eerste ondergrens"
    units = "m"  # TODO: @roger/job: peil is to mnap en geen m (in voorbeeld xml staat m)
    parameter_id = "Hpl.2b.0"
    timestamps = [
        TimestampColumns.eind_winter,
        TimestampColumns.begin_winter,
    ]


class XmlConstants:
    peilbesluitpeil = Peilbesluitpeil()
    eerste_ondergrens = EersteOndergrens()
    tweede_ondergrens = TweedeOndergrens()
    eerste_bovengrens = EersteBovengrens()
    tweede_bovengrens = TweedeBovengrens()
