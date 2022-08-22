from converter import constants
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List
from typing import TextIO

import csv
import logging


logger = logging.getLogger(__name__)

START_YEAR_PEILBESLUTIEN = 2008
END_YEAR_PEILBESLUTIEN = 2035
DUMMY_YEAR = 2000
DUMMY_STARTDATE = datetime(year=DUMMY_YEAR, month=1, day=1)
DUMMY_ENDDATE = datetime(year=DUMMY_YEAR, month=12, day=31)


class MargeType:
    peilbesluitpeil = "Peilbesluitpeil"
    peilbesluitpeil_eerste_bovengrens = "Peilbesluitpeil eerste bovengrens"
    peilbesluitpeil_tweede_bovengrens = "Peilbesluitpeil tweede bovengrens"
    peilbesluitpeil_eerste_ondergrens = "Peilbesluitpeil eerste ondergrens"
    peilbesluitpeil_tweede_ondergrens = "Peilbesluitpeil tweede ondergrens"


class ColumnBase:
    def __init__(self, name: str, min_value: any = None, max_value: any = None):
        self.name = name
        self.min_value = min_value
        self.max_value = max_value

    def validate(self, value: any):
        raise NotImplementedError


class GeneralColumn(ColumnBase):
    def __init__(self, target_dtype: type, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.target_dtype = target_dtype

    def validate(self, value: any):
        target_value = self.target_dtype(value)
        if self.min_value:
            assert target_value > self.min_value
        if self.max_value:
            assert target_value < self.max_value
        return target_value


class DateFormats(Enum):
    yyyymmdd = "%Y%M%d"
    dd_mm = "%d-%M"
    yyyy_dd_mm = "%Y-%d-%M"


class DateColumn(ColumnBase):
    def __init__(self, date_format: DateFormats, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.date_format = date_format

    def validate(self, value: str, year: int = None):
        """
        Examples:
            validate(value='20-12')                 returns (None, 12, 20)
            validate(value='20-12', year=2000)      returns (2000, 12, 20)
            validate(value='2000-20-12')            returns (2000, 12, 20)
            validate(value='2000-12-30')            returns Error (month 30 does not exists)
            validate(value='2000-12-30', year=2000) returns Error (either use year in arg value OR year)
        """
        assert isinstance(value, str)
        value_stripped = value.strip()

        assert isinstance(self.date_format, DateFormats)
        if self.date_format in (DateFormats.yyyymmdd, DateFormats.yyyy_dd_mm):
            assert not year, f"argument year {year} is not possible in combination with {self.date_format.value}"

        if self.date_format == DateFormats.dd_mm:  # 20-12
            year = year if year else DUMMY_YEAR
            date_obj = datetime.strptime(f"{year}-{value_stripped}", self.date_format.value)
        else:
            date_obj = datetime.strptime(f"{value_stripped}", self.date_format.value)

        if self.min_value:
            assert date_obj > self.min_value, f"{date_obj} must be greater than {self.min_value}"
        if self.max_value:
            assert date_obj < self.max_value, f"{date_obj} must be smaller than {self.max_value}"

        if self.date_format == DateFormats.dd_mm and not year:
            return None, date_obj.month, date_obj.day
        return date_obj.year, date_obj.month, date_obj.day


COLUMN_VALIDATORS = {
    "pgid": GeneralColumn(name="pgid", target_dtype=str),
    "startdatum": DateColumn(
        name="startdatum",
        date_format=DateFormats.yyyymmdd,
        min_value=datetime(year=START_YEAR_PEILBESLUTIEN, month=1, day=1),
        max_value=datetime.now(),
    ),  # 20190101
    "einddatum": DateColumn(
        name="einddatum",
        date_format=DateFormats.yyyymmdd,
        min_value=datetime(year=START_YEAR_PEILBESLUTIEN, month=1, day=1),
        max_value=datetime.now(),
    ),  # 20231023
    "eind_winter": DateColumn(
        name="eind_winter", date_format=DateFormats.dd_mm, min_value=DUMMY_STARTDATE, max_value=DUMMY_ENDDATE
    ),  # 01-04
    "begin_zomer": DateColumn(
        name="begin_zomer", date_format=DateFormats.dd_mm, min_value=DUMMY_STARTDATE, max_value=DUMMY_ENDDATE
    ),  # 01-05
    "eind_zomer": DateColumn(
        name="eind_zomer", date_format=DateFormats.dd_mm, min_value=DUMMY_STARTDATE, max_value=DUMMY_ENDDATE
    ),  # 01-09
    "begin_winter": DateColumn(
        name="begin_winter", date_format=DateFormats.dd_mm, min_value=DUMMY_STARTDATE, max_value=DUMMY_ENDDATE
    ),  # 01-10
    "zomerpeil": GeneralColumn(name="zomerpeil", target_dtype=float),  # 1.5
    "winterpeil": GeneralColumn(name="winterpeil", target_dtype=float),  # 1.25
    "_2e_marge_onder": GeneralColumn(name="_2e_marge_onder", target_dtype=float),  # 25
    "_1e_marge_onder": GeneralColumn(name="_1e_marge_onder", target_dtype=float),  # 10
    "_1e_marge_boven": GeneralColumn(name="_1e_marge_boven", target_dtype=float),  # 10
    "_2e_marge_boven": GeneralColumn(name="_2e_marge_boven", target_dtype=float),  # 25
}


class ConvertCsvToXml:
    def __init__(self, orig_csv_path: Path):
        self.orig_csv_path = orig_csv_path
        self._all_orig_csv_rows = None
        self._orig_csv_row_no_header = None
        self._orig_csv_header = None
        self._validated_csv_rows = None
        self._output_xml_path = None

    @property
    def all_orig_csv_rows(self):
        if self._all_orig_csv_rows is not None:
            return self._all_orig_csv_rows
        csv_stream = open(file=self.orig_csv_path.as_posix(), mode="r")
        delimiter_success = False
        delimiters_to_try = (";", ",")
        for delimiter in delimiters_to_try:
            csv_iterator = csv.reader(csv_stream, dialect="excel", delimiter=delimiter)
            csv_list = [x for x in csv_iterator]
            csv_stream.close()
            nr_columns_found = len(csv_list[-1])
            if nr_columns_found > 1:
                delimiter_success = True
                logger.info(f"reading csv with delimiter={delimiter}")
                break
        assert delimiter_success, f"could not open {self.orig_csv_path} with delimiters {delimiters_to_try}"
        self._all_orig_csv_rows = csv_list  # noqa
        return self._all_orig_csv_rows

    @property
    def orig_csv_row_no_header(self) -> List[List[str]]:
        if self._orig_csv_row_no_header is not None:
            return self._orig_csv_row_no_header
        self._orig_csv_row_no_header = [x for x in self.all_orig_csv_rows[1:]]
        return self._orig_csv_row_no_header

    @property
    def orig_csv_header(self) -> List[str]:
        if self._orig_csv_header is not None:
            return self._orig_csv_header
        self._orig_csv_header = self.all_orig_csv_rows[0]
        return self._orig_csv_header

    @property
    def validated_csv_rows(self) -> List[List[str]]:
        if self._validated_csv_rows is not None:
            return self._validated_csv_rows
        nr_expected_columns = len(self.orig_csv_header)
        index_warning = []
        index_error = []
        for row_index, row in enumerate(self.orig_csv_row_no_header):

            # check 1 (error) nr columns in this row must equal nr headers
            nr_columns = len(row)
            if nr_columns != nr_expected_columns:
                msg = f"nr columns in row {row_index} does not match length headers {self.orig_csv_header}"
                if constants.RAISE_ON_CSV_ERROR_ROW:
                    raise AssertionError(msg)
                logger.error(msg)
                index_error.append(row_index)

            # check 2 validate value
            for column_name, column_value in zip(self.orig_csv_header, row):
                column_validator = COLUMN_VALIDATORS[column_name]
                try:
                    column_validator.validate(value=column_value)
                except Exception as err:
                    column_validator.validate(value=column_value)
                    msg = f"could not convert {column_name} value {column_value}, err={err}"
                    raise AssertionError(msg)

        validated_row_indices = [x for x in range(0, len(self.orig_csv_row_no_header))]
        if not constants.INCLUDE_CSV_WARNING_ROWS_IN_XML:
            validated_row_indices = set(validated_row_indices).difference(set(index_warning))
        if not constants.INCLUDE_CSV_ERROR_ROWS_IN_XML:
            validated_row_indices = set(validated_row_indices).difference(set(index_error))
        validated_row_indices = tuple(validated_row_indices)
        self._validated_csv_rows = [self.orig_csv_row_no_header[x] for x in validated_row_indices]
        return self._validated_csv_rows

    @staticmethod
    def add_xml_first_rows(xml_file: TextIO) -> TextIO:
        xml_file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        xml_file.write(
            'TimeSeries xmlns="http://www.wldelft.nl/fews/PI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_timeseriesextended.xsd" version="1.2">\n'
        )
        xml_file.write("    <timeZone>1.0</timeZone>\n")
        return xml_file

    def convert_row(self, row):
        str_row = """<%s>%s</%s> \n""" * (len(header) - 1)
        str_row = """<%s>%s""" + "\n" + str_row + """</%s>"""
        var_values = [list_of_elments[k] for k in range(1, len(header)) for list_of_elments in [header, row, header]]
        var_values = [header[0], row[0]] + var_values + [header[0]]
        var_values = tuple(var_values)
        return str_row % var_values

    def run(self):
        a = self.validated_csv_rows
        now = datetime.now()
        xml_path = constants.DATA_OUTPUT_DIR / f"PeilbesluitPi_{now.strftime('%Y%m%d_%H%M%S')}.xml"
        with open(xml_path.as_posix(), mode="w") as xml_file:
            xml_file = self.add_xml_first_rows(xml_file=xml_file)

            for row in self.validated_csv_rows:
                for column_name, column_value in zip(self.orig_csv_header, row):
                    print(1)
        print(2)

    def create_and_save_xml(self):
        """
        <?xml version="1.0" encoding="UTF-8" ?>
        <TimeSeries xmlns="http://www.wldelft.nl/fews/PI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_timeseriesextended.xsd" version="1.2">
	    <timeZone>1.0</timeZone>
        <series>
            <header>
                <type>instantaneous</type>
             <locationId>PG0006</locationId>
                <parameterId>Hpl</parameterId>
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
        </series>
    	<series>
    	    ...
    	</series>


        """
        now = datetime.now()
        xml_path = constants.DATA_OUTPUT_DIR / f"PeilbesluitPi_{now.strftime('%Y%m%d_%H%M%S')}.xml"
        xml_file = open(xml_path.as_posix(), mode="w")

        xml_file.write("	<series>\n")
        xml_file.write("		<header>\n")
        xml_file.write("			<type>instantaneous</type>\n")
        xml_file.write("	<series>\n")
        xml_file.write("		<header>\n")
        xml_file.write("			<type>instantaneous</type>\n")
        xml_file.write('			<locationId>" + str(pgid) + "</locationId>\n')
        xml_file.write('			<parameterId>" + str(series[i]) + "</parameterId>\n')
        xml_file.write('			<timeStep unit="nonequidistant"/>\n')
        xml_file.write('		<startDate date="' + str(startdatum) + '" time="00:00:00"></startDate>\n')
        xml_file.write('		<endDate date="' + str(einddatum) + '" time="00:00:00"></endDate>\n')
        xml_file.write("			<missVal>-999.99</missVal>\n")
        xml_file.write('			<longName>" + str(description[i]) + "</longName>\n')
        xml_file.write("			<units>mNAP</units>\n")
        xml_file.write("			<sourceOrganisation></sourceOrganisation>\n")
        xml_file.write("			<sourceSystem>peilbesluit_invoer_tbv_WIS.csv</sourceSystem>\n")
        xml_file.write("			<fileDescription></fileDescription>\n")
        xml_file.write("			<region></region>\n")
        xml_file.write("		</header>\n")

        print(1)
        # text = """<collection shelf="New Arrivals">""" + "\n" + '\n'.join([convert_row(row) for row in data[1:]]) + "\n" + "</collection >"
        # print(text)
        with open(xml_path.as_posix(), mode="w") as xml_file:
            xml_file.write(header_text)

        print(2)
        # with open('output.xml', 'w') as myfile:
        #     myfile.write(text)

    # def run(self):
    #     self.create_and_save_xml()

    # for row in self.validated_csv_rows:
    #     print(1)
    #
    # print(2)

    # df = pd.read_csv('movies2.csv')
    # header = list(df.columns)
