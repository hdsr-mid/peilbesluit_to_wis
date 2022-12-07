from enum import Enum
from pathlib import Path

import numpy as np


# USER_SETINGS
O_drive = Path("O:/")
PEILMARGE_GIS_EXPORT_DIR = O_drive / "Planvorming\GIS\Peilbesluiten\Aanpak Actuele Peilbesluiten\Output FME-script"
PEILMARGE_GIS_EXPORT_FILE_PATH = PEILMARGE_GIS_EXPORT_DIR / "Koppeling_AAP_20221108.csv"
CREATE_XML = False


# BASE_DIR avoid 'Path.cwd()', as interactive_map.main() should be callable from everywhere
BASE_DIR = Path(__file__).parent.parent
CONVERTER_DIR = BASE_DIR / "converter"
DATA_DIR = CONVERTER_DIR / "data"
DATA_OUTPUT_DIR = DATA_DIR / "output"
DATA_EXAMPLE_DIR = DATA_DIR / "example"
LOG_DIR = DATA_OUTPUT_DIR / "log_rotating"
LOG_FILE_PATH = LOG_DIR / "main.log"
DATA_DIR_TEST_INPUT = CONVERTER_DIR / "tests" / "data" / "input"
PATH_CSV_TEST_INPUT = DATA_DIR_TEST_INPUT / "Koppeling_AAP_20221108.csv"
PATH_XML_TEST_EXPECTED_OUTPUT = DATA_DIR_TEST_INPUT / "expected_small.xml"

MIN_ALLOWED_MNAP = -10
MAX_ALLOWED_MNAP = 10
MIN_ALLOW_LOWER_MARGIN_CM = 0
MAX_ALLOW_LOWER_MARGIN_CM = 100 * 10  # yes... 10 meters
MIN_ALLOW_UPPER_MARGIN_CM = 0
MAX_ALLOW_UPPER_MARGIN_CM = 100 * 10  # yes... 10 meters
TAB = "    "


class ColumnNameDtypeConstants:
    col_pgid = "pgid"
    col_startdatum = "startdatum"
    col_einddatum = "einddatum"
    col_eind_winter = "eind_winter"
    col_begin_zomer = "begin_zomer"
    col_eind_zomer = "eind_zomer"
    col_begin_winter = "begin_winter"
    col_zomerpeil = "zomerpeil"
    col_winterpeil = "winterpeil"
    col_2e_marge_onder = "2e marge onder"
    col_1e_marge_onder = "1e marge onder"
    col_1e_marge_boven = "1e marge boven"
    col_2e_marge_boven = "2e marge boven"

    all_cols = [
        col_pgid,
        col_startdatum,
        col_einddatum,
        col_eind_winter,
        col_begin_zomer,
        col_eind_zomer,
        col_begin_winter,
        col_zomerpeil,
        col_winterpeil,
        col_2e_marge_onder,
        col_1e_marge_onder,
        col_1e_marge_boven,
        col_2e_marge_boven,
    ]

    dtypes = {
        col_pgid: str,
        col_startdatum: np.datetime64,
        col_einddatum: np.datetime64,
        col_eind_winter: str,
        col_begin_zomer: str,
        col_eind_zomer: str,
        col_begin_winter: str,
        col_zomerpeil: float,
        col_winterpeil: float,
        col_2e_marge_onder: int,
        col_1e_marge_onder: int,
        col_1e_marge_boven: int,
        col_2e_marge_boven: int,
    }


class DateFormats(Enum):
    yyyymmdd = "%Y%m%d"  # 20001231
    dd_mm = "%d-%m"  # 31-12
    yyyy_dd_mm = "%Y-%d-%m"  # 2000-31-12
    yyyy_mm_dd = "%Y-%m-%d"  # 2000-12-31


class TimestampColumns:
    eind_winter = ColumnNameDtypeConstants.col_eind_winter
    begin_zomer = ColumnNameDtypeConstants.col_begin_zomer
    eind_zomer = ColumnNameDtypeConstants.col_eind_winter
    begin_winter = ColumnNameDtypeConstants.col_begin_winter


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


def check_constants():
    assert CONVERTER_DIR.is_dir()
    assert DATA_DIR.is_dir()
    assert DATA_OUTPUT_DIR.is_dir()
    assert LOG_DIR.is_dir()
    assert PEILMARGE_GIS_EXPORT_FILE_PATH.is_file()
    assert PATH_CSV_TEST_INPUT.is_file()
    assert PATH_XML_TEST_EXPECTED_OUTPUT.is_file()


check_constants()
