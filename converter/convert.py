from converter import constants
from converter.xml_builder import XmlSeriesBuilder
from datetime import datetime
from enum import Enum
from pathlib import Path

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
        self._csv_rows_no_error = None
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
    def orig_csv_row_no_header(self) -> list:
        if self._orig_csv_row_no_header is not None:
            return self._orig_csv_row_no_header
        self._orig_csv_row_no_header = [x for x in self.all_orig_csv_rows[1:]]
        return self._orig_csv_row_no_header

    @property
    def orig_csv_header(self) -> list:
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
        error_peilgebied: set = None,
    ):
        if error_dict_index is not None:
            if row_index not in error_dict_index:
                error_dict_index[row_index] = {error_type_id: msg}
            else:
                error_dict_index[row_index][error_type_id] = msg
        if error_peilgebied is not None:
            error_peilgebied.add(peilgebied_id)
        return error_dict_index, error_peilgebied

    @classmethod
    def get_value(cls, col_name: str, zipped_cols_values, convert_to_target: bool = True) -> any:
        col_name, value = [x for x in zipped_cols_values if x[0] == col_name][0]
        validator = COLUMN_VALIDATORS[col_name]
        validated_value = validator.validate(value=value)
        return validated_value if convert_to_target else value

    @property
    def csv_rows_no_error(self) -> list:
        if self._csv_rows_no_error is not None:
            return self._csv_rows_no_error
        logger.info(f"validating {self.orig_csv_path}")
        nr_expected_columns = len(self.orig_csv_header)
        error_dict_index = {}
        error_peilgebied = set()
        for row_index, row in enumerate(self.orig_csv_row_no_header):

            error_type_id = 1
            zipped_cols_values = [x for x in zip(self.orig_csv_header, row)]
            peilgebied_id = self.get_value(col_name="pgid", zipped_cols_values=zipped_cols_values)

            logger.debug("check 1 (error) nr columns in this row must equal nr headers")
            nr_columns = len(row)
            if nr_columns != nr_expected_columns:
                msg = f"nr cells does not match nr csv columns {self.orig_csv_header}"
                if constants.RAISE_ON_CSV_ERROR_ROW:
                    raise AssertionError(msg)
                logger.error(msg)
                error_dict_index, error_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=error_type_id,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_peilgebied=error_peilgebied,
                )
                continue

            logger.debug("check 2 validate values")
            for column_name, column_value in zipped_cols_values:
                error_type_id += 1
                column_validator = COLUMN_VALIDATORS[column_name]
                try:
                    column_validator.validate(value=column_value)
                except Exception as err:
                    msg = f"column={column_name}, err={err}"
                    if constants.RAISE_ON_CSV_ERROR_ROW:
                        raise AssertionError(msg)

                    error_dict_index, error_peilgebied = self.save_error(
                        row_index=row_index,
                        error_type_id=error_type_id,
                        error_dict_index=error_dict_index,
                        msg=msg,
                        peilgebied_id=peilgebied_id,
                        error_peilgebied=error_peilgebied,
                    )

        logger.debug("check 3: validate values (dates) with other values in same row")
        for row_index, row in enumerate(self.orig_csv_row_no_header):
            if row_index in error_dict_index:
                continue

            zipped_cols_values = [x for x in zip(self.orig_csv_header, row)]
            peilgebied_id = self.get_value(col_name="pgid", zipped_cols_values=zipped_cols_values)
            if peilgebied_id in error_peilgebied:
                continue

            # check 3a: peilen onderling
            eind_winter = self.get_value(col_name="eind_winter", zipped_cols_values=zipped_cols_values)
            begin_zomer = self.get_value(col_name="begin_zomer", zipped_cols_values=zipped_cols_values)
            eind_zomer = self.get_value(col_name="eind_zomer", zipped_cols_values=zipped_cols_values)
            begin_winter = self.get_value(col_name="begin_winter", zipped_cols_values=zipped_cols_values)
            dates_are_ordered_ok = eind_winter < begin_zomer < eind_zomer < begin_winter
            if not dates_are_ordered_ok:
                msg = f"dates are not ordered (eind_winter < begin_zomer < eind_zomer < begin_winter)"
                error_dict_index, error_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=len(self.orig_csv_header) + 1,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_peilgebied=error_peilgebied,
                )

            # check 3b: validate bovenmarges onderling
            _2e_marge_boven = self.get_value(col_name="2e_marge_boven", zipped_cols_values=zipped_cols_values)
            _1e_marge_boven = self.get_value(col_name="1e_marge_boven", zipped_cols_values=zipped_cols_values)
            boven_marges_are_ok = 0 < _1e_marge_boven < _2e_marge_boven
            if not boven_marges_are_ok:
                msg = f"boven marges are wrong, we expected 0 < _1e_marge_boven < _2e_marge_boven"
                error_dict_index, error_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=len(self.orig_csv_header) + 2,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_peilgebied=error_peilgebied,
                )

            # check 3c: validate ondermarges onderling
            _2e_marge_onder = self.get_value(col_name="2e_marge_onder", zipped_cols_values=zipped_cols_values)
            _1e_marge_onder = self.get_value(col_name="1e_marge_onder", zipped_cols_values=zipped_cols_values)
            onder_marges_are_ok = 0 < _1e_marge_onder < _2e_marge_onder
            if not onder_marges_are_ok:
                msg = f"onder marges are wrong, we expected 0 < _1e_marge_onder < _2e_marge_onder"
                error_dict_index, error_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=len(self.orig_csv_header) + 3,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_peilgebied=error_peilgebied,
                )

        logger.debug(f"check 4: subsequent rows of the same pgid must connect (no gap, and no overlap")
        index_pgid_column = self.orig_csv_header.index("pgid")
        all_pgids = [x[index_pgid_column] for x in self.orig_csv_row_no_header]
        pgid_dict = {}

        # build dict
        for index, pgid in enumerate(all_pgids):
            if pgid in pgid_dict:
                pgid_dict[pgid] += [index]
            else:
                pgid_dict[pgid] = [index]

        # loop trough dict to compare csv rows with the same pgid
        for pgid, indices in pgid_dict.items():
            if len(indices) <= 1:
                # nothing to compare
                continue
            pgid_rows = [self.orig_csv_row_no_header[x] for x in indices]
            previous_enddate = None
            for pgid_row, row_index in zip(pgid_rows, indices):
                zipped_cols_values = [x for x in zip(self.orig_csv_header, pgid_row)]
                startdate = self.get_value(col_name="startdatum", zipped_cols_values=zipped_cols_values)
                enddate = self.get_value(col_name="einddatum", zipped_cols_values=zipped_cols_values)
                if previous_enddate and startdate != previous_enddate:
                    msg = f"startdate {startdate} must equal previous_enddate {previous_enddate}"
                    error_dict_index, error_peilgebied = self.save_error(
                        row_index=row_index,
                        error_type_id=len(self.orig_csv_header) + 4,
                        error_dict_index=error_dict_index,
                        msg=msg,
                        peilgebied_id=pgid,
                        error_peilgebied=error_peilgebied,
                    )
                previous_enddate = enddate

        logger.debug("check 5: filter out all rows of same peilgebied id if =>1 row with that peilgebied id is wrong")
        for row_index, row in enumerate(self.orig_csv_row_no_header):
            if row_index in error_dict_index.keys():
                # this row is already excluded
                continue

            zipped_cols_values = [x for x in zip(self.orig_csv_header, row)]
            peilgebied_id = self.get_value(col_name="pgid", zipped_cols_values=zipped_cols_values)

            if peilgebied_id in error_peilgebied:
                msg = f"skip this okay row as in other row(s) this pgid has an error"
                error_dict_index, error_peilgebied = self.save_error(
                    row_index=row_index,
                    error_type_id=len(self.orig_csv_header) + 5,
                    error_dict_index=error_dict_index,
                    msg=msg,
                    peilgebied_id=peilgebied_id,
                    error_peilgebied=error_peilgebied,
                )
                continue

        row_indices_no_error = [x for x in range(0, len(self.orig_csv_row_no_header)) if x not in error_dict_index]
        self._csv_rows_no_error = [self.orig_csv_row_no_header[x] for x in row_indices_no_error]
        nr_deleted_rows = len(self.orig_csv_row_no_header) - len(self._csv_rows_no_error)
        logger.info(f"found {nr_deleted_rows} rows with error (nr rows left over = {len(row_indices_no_error)})")

        _now = datetime.now().strftime("%Y%m%d_%H%M%S")
        max_error_type_id = max(
            [inner_key for value in error_dict_index.values() for inner_key, inner_value in value.items()]
        )

        if constants.CREATE_CSV_WITH_ERRORS:
            error_file_path = constants.DATA_OUTPUT_DIR / f"{self.orig_csv_path.stem}_errors_{_now}.csv"
            logger.info(f"create error csv (orig csv + 1 column with errors) at {error_file_path}")
            csvoutput = open(file=error_file_path, mode="w")
            writer = csv.writer(csvoutput, delimiter=",", lineterminator="\n")

            error_columns = ["has_error"] + [f"error_{x}" for x in range(1, max_error_type_id + 1)]
            column_names = self.orig_csv_header + error_columns
            writer.writerow(column_names)
            for row_index, orig_row in enumerate(self.orig_csv_row_no_header):
                errors = error_dict_index.get(row_index, "")
                if not errors:
                    has_error = False
                    writer.writerow(orig_row + [has_error])
                    continue
                has_error = True
                error_list = [has_error] + [""] * max_error_type_id
                for error_type_id, error in errors.items():
                    error = error.replace(",", " ")
                    error_list[error_type_id] = error
                writer.writerow(orig_row + error_list)
            csvoutput.close()

        return self._csv_rows_no_error

    @staticmethod
    def add_xml_first_rows(xml_file):
        xml_file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        xml_file.write(
            'TimeSeries xmlns="http://www.wldelft.nl/fews/PI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_timeseriesextended.xsd" version="1.2">\n'
        )
        xml_file.write("    <timeZone>1.0</timeZone>\n")
        return xml_file

    def add_xml_series(self, xml_file, all_rows_same_pgid, _func):
        """Add one xml series build from one or more csv rows"""
        xml_builder = None
        nr_all_rows_same_pgid = len(all_rows_same_pgid)
        for index, csv_row in enumerate(all_rows_same_pgid):
            is_first_pgid_csv_row = index == 0
            is_last_pgid_csv_row = index == nr_all_rows_same_pgid - 1
            kwargs = dict(zip(self.orig_csv_header, csv_row))
            xml_builder = XmlSeriesBuilder(
                xml_file=xml_file,
                is_first_pgid_csv_row=is_first_pgid_csv_row,
                is_last_pgid_csv_row=is_last_pgid_csv_row,
                **kwargs,
            )
            xml_builder_method = getattr(xml_builder, _func.__name__)
            xml_builder_method()
        return xml_builder.xml_file

    def run(self):
        if constants.CREATE_CSV_WITH_ERRORS:
            _ = self.csv_rows_no_error
        else:
            logger.info("skip creating csv with errors")

        if not constants.CREATE_XML:
            logger.info("skip creating xml")
            return
        xml_path = constants.DATA_OUTPUT_DIR / f"PeilbesluitPi_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xml"
        xml_file = open(xml_path.as_posix(), mode="w")
        xml_file = self.add_xml_first_rows(xml_file=xml_file)
        pgid_done = []
        for row in self.csv_rows_no_error:
            kwargs = dict(zip(self.orig_csv_header, row))
            pgid = kwargs["pgid"]
            if pgid in pgid_done:
                continue
            all_rows_same_pgid = []
            for _row in self.csv_rows_no_error:
                zipped_cols_values = [x for x in zip(self.orig_csv_header, _row)]
                peilgebied_id = self.get_value(col_name="pgid", zipped_cols_values=zipped_cols_values)
                if peilgebied_id == pgid:
                    all_rows_same_pgid.append(_row)
            for _func in (
                XmlSeriesBuilder.add_series_peilbesluitpeil,
                XmlSeriesBuilder.add_series_eerste_ondergrens,
                XmlSeriesBuilder.add_series_tweede_ondergrens,
                XmlSeriesBuilder.add_series_eerste_bovengrens,
                XmlSeriesBuilder.add_series_tweede_bovengrens,
            ):
                xml_file = self.add_xml_series(xml_file=xml_file, all_rows_same_pgid=all_rows_same_pgid, _func=_func)
        xml_file.close()
