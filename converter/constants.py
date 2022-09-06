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
    / "Planvorming\Gebiedsgerichte_plannen\Peilbesluiten\Algemeen\Peilbesluitevaluatie\Product script Inger - peilen, marges en datum"
)
PEILMARGE_GIS_EXPORT_FILE_PATH = PEILMARGE_GIS_EXPORT_DIR / "Peilbesluitpeilen2019_1107.csv"

CREATE_CSV_WITH_ERRORS = False
CREATE_XML = False
INCLUDE_CSV_WARNING_ROWS_IN_XML = False
INCLUDE_CSV_ERROR_ROWS_IN_XML = True
RAISE_ON_CSV_WARNING_ROW = False
RAISE_ON_CSV_ERROR_ROW = False

"""
pgid	startdatum	einddatum	eind_winter	begin_zomer	eind_zomer	begin_winter	zomerpeil	winterpeil	2e marge onder	1e marge onder	1e marge boven	2e marge boven
PG0566	20190101	20231023	01-04	    01-05	    01-09	    01-10	        1.5	        1.25	    25	            10	            10              25
PG2077	20190101	20231031	01-04	    01-05	    01-09	    01-10	        915	        915	        25	            50.5	        50.5	        25
"""

"""
bovenstaande wordt omgezet naar xml

<?xml version="1.0" encoding="UTF-8" ?>
<TimeSeries xmlns="http://www.wldelft.nl/fews/PI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_timeseriesextended.xsd" version="1.2">
	<timeZone>1.0</timeZone>
	<series>
		<header>
			<type>instantaneous</type>
         <locationId>PG0566</locationId>
			<parameterId> ??? </parameterId>
			<timeStep unit="nonequidistant"/>
			<startDate date="1990-01-01" time="00:00:00"></startDate>
			<endDate date="2024-12-31" time="00:00:00"></endDate>
			<missVal>-999.99</missVal>
			<longName>Peilbesluitpeil</longName>
			<units>m</units>
			<sourceOrganisation></sourceOrganisation>
			<sourceSystem>tijdreeks FEWS-PI.xls</sourceSystem>
			<fileDescription></fileDescription>
			<region></region>
		</header>
		<event date="1990-01-01" time="00:00:00" value="0.80" flag="0"/>
		<event date="1990-04-01" time="00:00:00" value="0.95" flag="0"/>
		<event date="1990-05-01" time="00:00:00" value="1.10" flag="0"/>
		<event date="1990-09-01" time="00:00:00" value="0.95" flag="0"/>
		<event date="1990-10-01" time="00:00:00" value="0.80" flag="0"/>
		

"""

MIN_ALLOWED_MNAP = -10
MAX_ALLOWED_MNAP = 10
MAX_ALLOW_LOWER_MARGIN_CM = 50
MAX_ALLOW_UPPER_MARGIN_CM = 50


def get_last_gis_export_peilmarges_csv() -> Path:
    list_of_files = glob.glob(pathname=(PEILMARGE_GIS_EXPORT_DIR / "*.csv").as_posix())
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
