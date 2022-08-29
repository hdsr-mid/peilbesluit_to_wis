from converter import constants
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import List
from typing import TextIO

import csv
import logging


logger = logging.getLogger(__name__)

START_YEAR_PEILBESLUTIEN = 2000
END_YEAR_PEILBESLUTIEN = 2035
DUMMY_YEAR = 2000
DUMMY_STARTDATE = datetime(year=DUMMY_YEAR, month=1, day=1)
DUMMY_ENDDATE = datetime(year=DUMMY_YEAR, month=12, day=31)
MIN_PEIL = -10  # [mnap]
MAX_PEIL = 10  # [mnap]
MIN_MARGE = 1  # [cm]
MAX_MARGE = 100  # [cm]


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
        try:
            target_value = self.target_dtype(value)
        except Exception:
            raise AssertionError(
                f"could not convert column {self.name} value '{value}' to target_dtype {self.target_dtype}"
            )

        if self.min_value:
            assert target_value > self.min_value, f"value '{value}' must be larger than {self.min_value}"
        if self.max_value:
            assert target_value < self.max_value, f"value '{value}' must be smaller than {self.max_value}"
        return target_value


class DateFormats(Enum):
    yyyymmdd = "%Y%m%d"
    dd_mm = "%d-%m"
    yyyy_dd_mm = "%Y-%d-%m"


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

        try:
            if self.date_format == DateFormats.dd_mm:  # 20-12
                year = year if year else DUMMY_YEAR
                date_obj = datetime.strptime(f"{year}-{value_stripped}", DateFormats.yyyy_dd_mm.value)
            else:
                date_obj = datetime.strptime(f"{value_stripped}", self.date_format.value)
        except Exception as err:
            raise AssertionError(f"could not transform date_string {value_stripped} to date_object, err={err}")

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
        max_value=datetime(year=END_YEAR_PEILBESLUTIEN, month=12, day=31),
    ),  # 20190101
    "einddatum": DateColumn(
        name="einddatum",
        date_format=DateFormats.yyyymmdd,
        min_value=datetime(year=START_YEAR_PEILBESLUTIEN, month=1, day=1),
        max_value=datetime(year=END_YEAR_PEILBESLUTIEN, month=12, day=31),
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
    "zomerpeil": GeneralColumn(name="zomerpeil", target_dtype=float, min_value=MIN_PEIL, max_value=MAX_PEIL),  # 1.5
    "winterpeil": GeneralColumn(name="winterpeil", target_dtype=float, min_value=MIN_PEIL, max_value=MAX_PEIL),  # 1.25
    "2e_marge_onder": GeneralColumn(
        name="_2e_marge_onder", target_dtype=float, min_value=MIN_MARGE, max_value=MAX_MARGE
    ),  # 25
    "1e_marge_onder": GeneralColumn(
        name="_1e_marge_onder", target_dtype=float, min_value=MIN_MARGE, max_value=MAX_MARGE
    ),  # 10
    "1e_marge_boven": GeneralColumn(
        name="_1e_marge_boven", target_dtype=float, min_value=MIN_MARGE, max_value=MAX_MARGE
    ),  # 10
    "2e_marge_boven": GeneralColumn(
        name="_2e_marge_boven", target_dtype=float, min_value=MIN_MARGE, max_value=MAX_MARGE
    ),  # 25
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
        self._orig_csv_header = [x.replace(" ", "_").strip() for x in self.all_orig_csv_rows[0]]
        return self._orig_csv_header

    @classmethod
    def save_error(
        cls,
        row_index: int,
        error_type_id: int,
        msg: str,
        peilgebied_id: str,
        error_dict_index: dict = None,
        error_dict_peilgebied: dict = None,
    ):
        error_type_id_str = f"error_type_id={error_type_id}"
        if error_dict_index:
            if row_index not in error_dict_index:
                error_dict_index[row_index] = {error_type_id_str: msg}
            else:
                error_dict_index[row_index][error_type_id_str] = msg

        if error_dict_peilgebied:
            if peilgebied_id not in error_dict_peilgebied:
                error_dict_peilgebied[peilgebied_id] = {error_type_id_str: msg}
            else:
                error_dict_peilgebied[peilgebied_id][error_type_id_str] = msg
        return error_dict_index, error_dict_peilgebied

    @property
    def validated_csv_rows(self) -> List[List[str]]:
        if self._validated_csv_rows is not None:
            return self._validated_csv_rows
        nr_expected_columns = len(self.orig_csv_header)
        error_dict_index = {}
        error_dict_peilgebied = {}
        for row_index, row in enumerate(self.orig_csv_row_no_header):
            error_type_id = 1
            zipped_data = [x for x in zip(self.orig_csv_header, row)]
            peilgebied_id = [column_value for column_name, column_value in zipped_data if column_name == "pgid"][0]

            logger.info("check 1 (error) nr columns in this row must equal nr headers")
            nr_columns = len(row)
            if nr_columns != nr_expected_columns:
                msg = f"Skipping csv row {row_index}, err=nr cells does not match nr csv columns {self.orig_csv_header}"
                if constants.RAISE_ON_CSV_ERROR_ROW:
                    raise AssertionError(msg)
                logger.error(msg)
                error_dict_index, error_dict_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=error_type_id,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_dict_peilgebied=error_dict_peilgebied,
                )
                continue

            logger.debug("check 2 validate values")
            for column_name, column_value in zipped_data:
                error_type_id += 1
                column_validator = COLUMN_VALIDATORS[column_name]
                try:
                    column_validator.validate(value=column_value)
                except Exception as err:
                    msg = f"Skipping csv row {row_index}, column={column_name}, err={err}"
                    if constants.RAISE_ON_CSV_ERROR_ROW:
                        raise AssertionError(msg)

                    error_dict_index, error_dict_peilgebied = self.save_error(
                        row_index=row_index,
                        error_type_id=error_type_id,
                        error_dict_index=error_dict_index,
                        msg=msg,
                        peilgebied_id=peilgebied_id,
                        error_dict_peilgebied=error_dict_peilgebied,
                    )

        logger.debug("check 3: validate values (dates) with other values in same row")
        error_type_id = len(self.orig_csv_header) + 1
        for row_index, row in enumerate(self.orig_csv_row_no_header):
            if row_index in error_dict_index:
                continue

            zipped_data = [x for x in zip(self.orig_csv_header, row)]
            peilgebied_id = [column_value for column_name, column_value in zipped_data if column_name == "pgid"][0]
            if peilgebied_id in error_dict_peilgebied:
                continue

            # check 3a: peilen onderling
            eind_winter = COLUMN_VALIDATORS["eind_winter"].validate(
                value=[column_value for column_name, column_value in zipped_data if column_name == "eind_winter"][0]
            )
            begin_zomer = COLUMN_VALIDATORS["begin_zomer"].validate(
                value=[column_value for column_name, column_value in zipped_data if column_name == "begin_zomer"][0]
            )
            eind_zomer = COLUMN_VALIDATORS["eind_zomer"].validate(
                value=[column_value for column_name, column_value in zipped_data if column_name == "eind_zomer"][0]
            )
            begin_winter = COLUMN_VALIDATORS["begin_winter"].validate(
                value=[column_value for column_name, column_value in zipped_data if column_name == "begin_winter"][0]
            )
            dates_are_ordered_ok = eind_winter < begin_zomer < eind_zomer < begin_winter
            if not dates_are_ordered_ok:
                msg = (
                    f"Skipping csv row {row_index} as dates are not ordered "
                    f"(eind_winter < begin_zomer < eind_zomer < begin_winter)"
                )
                error_dict_index, error_dict_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=error_type_id,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_dict_peilgebied=error_dict_peilgebied,
                )

            # check 3b: validate bovenmarges onderling
            error_type_id += 1
            _2e_marge_boven = COLUMN_VALIDATORS["2e_marge_boven"].validate(
                value=[column_value for column_name, column_value in zipped_data if column_name == "2e_marge_boven"][0]
            )
            _1e_marge_boven = COLUMN_VALIDATORS["1e_marge_boven"].validate(
                value=[column_value for column_name, column_value in zipped_data if column_name == "1e_marge_boven"][0]
            )
            try:
                boven_marges_are_ok = 0 < _1e_marge_boven < _2e_marge_boven
            except Exception:
                boven_marges_are_ok = False
            if not boven_marges_are_ok:
                msg = f"Skipping csv row {row_index} as boven marges are wrong (expected 0 < _1e_marge_boven < _2e_marge_boven)"
                error_dict_index, error_dict_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=error_type_id,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_dict_peilgebied=error_dict_peilgebied,
                )

            # check 3c: validate ondermarges onderling
            error_type_id += 1
            _2e_marge_onder = COLUMN_VALIDATORS["2e_marge_onder"].validate(
                value=[column_value for column_name, column_value in zipped_data if column_name == "2e_marge_onder"][0]
            )
            _1e_marge_onder = COLUMN_VALIDATORS["1e_marge_onder"].validate(
                value=[column_value for column_name, column_value in zipped_data if column_name == "1e_marge_onder"][0]
            )
            onder_marges_are_ok = 0 < _1e_marge_onder < _2e_marge_onder
            if not onder_marges_are_ok:
                msg = f"Skipping csv row {row_index} as boven marges are wrong (expected 0 < _1e_marge_onder < _2e_marge_onder)"
                error_dict_index, error_dict_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=error_type_id,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_dict_peilgebied=error_dict_peilgebied,
                )

        logger.debug("check 4: filter out all rows of same peilgebied id if =>1 row with that peilgebied id is wrong")
        error_type_id += 1
        for row_index, row in enumerate(self.orig_csv_row_no_header):
            if row_index in error_dict_index:
                continue

            zipped_data = [x for x in zip(self.orig_csv_header, row)]
            peilgebied_id = [column_value for column_name, column_value in zipped_data if column_name == "pgid"][0]

            if peilgebied_id in error_dict_peilgebied:
                msg = f"skip this okay row (pgid={peilgebied_id}) as in other rows this pgid has an error"
                error_dict_index, error_dict_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=error_type_id,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_dict_peilgebied=None,
                )
                continue

        row_indices_no_error = [x for x in range(0, len(self.orig_csv_row_no_header)) if x not in error_dict_index]
        self._validated_csv_rows = [self.orig_csv_row_no_header[x] for x in row_indices_no_error]
        nr_deleted_rows = len(self.orig_csv_row_no_header) - len(self._validated_csv_rows)
        logger.info(f"deleted {nr_deleted_rows} rows (, nr rows left over = {len(row_indices_no_error)}")

        _now = f"%Y%m%d_%H%M%S"

        # create csv with error_dict_index
        file_path = constants.DATA_OUTPUT_DIR / f"{datetime.now().strftime('%Y%m%d_%H%M%S')}_row_id).csv"
        with open(file_path, mode="w") as error_csv1:
            csv_writer = csv.writer(
                error_csv1,
                delimiter="\t",
                lineterminator="\n",
            )
            headers = ["orig_row_index", "error_type_id", "error_msg"]
            csv_writer.writerow(headers)
            for orig_row_index, error_dict in error_dict_index.items():
                for error_type_id, error_msg in error_dict.items():
                    csv_writer.writerow([orig_row_index, error_type_id, error_msg])
            error_csv1.close()

        # create csv with error_dict_index
        file_path = constants.DATA_OUTPUT_DIR / f"{datetime.now().strftime(f'{_now}_peilgebied_id')}.csv"
        with open(file_path, mode="w") as error_csv2:
            csv_writer = csv.writer(
                error_csv2,
                delimiter="\t",
                lineterminator="\n",
            )
            headers = ["pgid", "error_type_id", "error_msg"]
            csv_writer.writerow(headers)
            for orig_row_index, error_dict in error_dict_peilgebied.items():
                for error_type_id, error_msg in error_dict.items():
                    csv_writer.writerow([error_dict_peilgebied, error_type_id, error_msg])
            error_csv2.close()

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
        xml_path = constants.DATA_OUTPUT_DIR / f"PeilbesluitPi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        with open(xml_path.as_posix(), mode="w") as xml_file:
            xml_file = self.add_xml_first_rows(xml_file=xml_file)

            for row in self.validated_csv_rows:
                for column_name, column_value in zip(self.orig_csv_header, row):
                    pass
                    # print(1)
        # print(2)

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
