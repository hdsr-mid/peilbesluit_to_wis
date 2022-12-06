from converter import constants
from converter.constants import ColumnNameDtypeConstants
from converter.constants import TAB
from converter.utils import DatesColumns
from converter.utils import get_progress
from converter.xml_builder import XmlSeriesBuilder
from datetime import datetime
from hdsr_wis_config_reader.utils import PdReadFlexibleCsv
from pathlib import Path
from typing import Optional
from typing import Tuple

import logging
import pandas as pd


logger = logging.getLogger(__name__)


class CsvError:
    def __init__(self, csv_row: int, pgid: str, error_msg: str):
        self.csv_row = csv_row
        self.pgid = pgid
        self.error_msg = error_msg
        assert "," not in error_msg, "code error. avoid ',' in value (difficult in excel)"


class ConvertCsvToXml(ColumnNameDtypeConstants):
    def __init__(self, orig_csv_path: Path):
        self.orig_csv_path = orig_csv_path
        self._df = None
        self._csv_rows_no_error = None
        self._output_xml_path = None
        self._outputdir = None
        self.datecolumn_start = DatesColumns(
            column_name=self.col_startdatum, date_format=constants.DateFormats.yyyymmdd.value, errors="raise"
        )
        self.datecolumn_eind = DatesColumns(
            column_name=self.col_einddatum, date_format=constants.DateFormats.yyyymmdd.value, errors="raise"
        )

    @property
    def df(self) -> pd.DataFrame:
        if self._df is not None:
            return self._df
        reader = PdReadFlexibleCsv(
            path=self.orig_csv_path.as_posix(),
            date_columns=[self.datecolumn_start, self.datecolumn_eind],
            expected_columns=self.all_cols,
        )
        self._df = reader.df

        # check dtypes
        logger.info(f"validate colums and dtype csv {self.orig_csv_path}")
        for col, dtype in self.dtypes.items():
            try:
                self._df[col] = self._df[col].astype(dtype)
            except Exception as err:
                logger.error(f"could not convert col {col} to dtype {dtype} because of {err}")
        return self._df

    @property
    def output_dir(self) -> Path:
        if self._outputdir:
            return self._outputdir
        datetime_str_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._outputdir = constants.DATA_OUTPUT_DIR / datetime_str_now
        self._outputdir.mkdir(parents=True, exist_ok=False)
        return self._outputdir

    @staticmethod
    def get_month_day_from_string(datestr_m_d: str) -> Tuple[int, int]:
        fmt = constants.DateFormats.dd_mm.value
        try:
            date_obj = pd.to_datetime(datestr_m_d, format=fmt)
        except Exception:
            raise AssertionError(
                f"we expected date format '{fmt}' so e.g. '01-04' (in other words: April 1), but "
                f"found {datestr_m_d}"
            )
        return date_obj.month, date_obj.day

    def get_dummy_date(self, dummy_year: int, datestr_m_d: str) -> pd.Timestamp:
        month, day = self.get_month_day_from_string(datestr_m_d)
        date_obj = pd.Timestamp(year=dummy_year, month=month, day=day)
        return date_obj

    def validate_df(self) -> None:
        """
        # noqa  pgid	startdatum	einddatum	eind_winter	begin_zomer	eind_zomer	begin_winter	zomerpeil	winterpeil	2e marge onder	1e marge onder	1e marge boven	2e marge boven
        # noqa  PG0003	20220101	20221231	1-Apr	    1-May	    1-Sep	    1-Oct	        0.15        -0.15	    25	            10	            10	            25
        # noqa  PG0006	20220101	20221231	1-Apr	    1-May	    1-Sep	    1-Oct	        1.1	        0.8	        25	            10	            10	            25
        # noqa  PG0008	20220101	20221231	1-Apr	    1-May	    1-Sep	    1-Oct	        1.2	        1	        25	            10	            10	            25
        # noqa  PG0010	20220101	20221231	1-Apr	    1-May	    1-Sep	    1-Oct	        1.65        1.45	    25	            10	            10	            25
        # noqa  PG0012	20220101	20221231	1-Apr	    1-May	    1-Sep	    1-Oct	        2	        2	        25	            10	            10	            25
        """
        assert not self.df.empty
        logger.info(f"specific validating csv {self.orig_csv_path}")

        # We already validated if columns exist and dtypes
        error_list = []  # {<csv_row_index>:<error_message>}
        for index, row in self.df.iterrows():

            pgid = row[self.col_pgid]

            # check 1: ensure that dates in 1 row are ordered (eind_winter < begin_zomer < eind_zomer < begin_winter)
            try:
                eind_winter = self.get_dummy_date(dummy_year=2000, datestr_m_d=row[self.col_eind_winter])
                begin_zomer = self.get_dummy_date(dummy_year=2000, datestr_m_d=row[self.col_begin_zomer])
                eind_zomer = self.get_dummy_date(dummy_year=2000, datestr_m_d=row[self.col_eind_zomer])
                begin_winter = self.get_dummy_date(dummy_year=2000, datestr_m_d=row[self.col_begin_winter])
            except Exception as err:
                raise AssertionError(f"could not get dates from row {index}, err={err}")
            dates_are_ordered_ok = eind_winter < begin_zomer < eind_zomer < begin_winter
            if not dates_are_ordered_ok:
                raise AssertionError(f"dates are not ordered, row={index}")

            # check 2: validate onder marges per row

            _min = constants.MIN_ALLOW_LOWER_MARGIN_CM
            _max = constants.MAX_ALLOW_LOWER_MARGIN_CM
            try:
                boven_marges_are_ok = _min <= row[self.col_1e_marge_onder] <= row[self.col_2e_marge_onder] <= _max
                if not boven_marges_are_ok:
                    msg = f"invalid onder marges as we expected {_min} <= _1e_marge_onder <= _2e_marge_onder <= {_max}"
                    error_list.append(CsvError(csv_row=index, pgid=pgid, error_msg=msg))
            except KeyError:
                error_list.append(CsvError(csv_row=index, pgid=pgid, error_msg="onder marges could not be checked"))

            # check 3: validate boven marges per row
            _min = constants.MIN_ALLOW_UPPER_MARGIN_CM
            _max = constants.MAX_ALLOW_UPPER_MARGIN_CM
            try:
                boven_marges_are_ok = _min <= row[self.col_1e_marge_boven] <= row[self.col_2e_marge_boven] <= _max
                if not boven_marges_are_ok:
                    msg = f"invalid boven marges as we expected {_min} <= _1e_marge_boven <= _2e_marge_boven <= {_max}"
                    error_list.append(CsvError(csv_row=index, pgid=pgid, error_msg=msg))
            except KeyError:
                error_list.append(CsvError(csv_row=index, pgid=pgid, error_msg="boven marges could not be checked"))

            # check 4: check peilen
            _min = constants.MIN_ALLOWED_MNAP
            _max = constants.MAX_ALLOWED_MNAP
            zomerpeil_ok = _min <= row[self.col_zomerpeil] <= _max
            if not zomerpeil_ok:
                msg = f"invalid zomerpeil as we expected {_min} <= zomerpeil <= {_max}"
                error_list.append(CsvError(csv_row=index, pgid=pgid, error_msg=msg))
            winterpeil_ok = _min <= row[self.col_winterpeil] <= _max
            if not winterpeil_ok:
                msg = f"invalid winterpeil as we expected {_min} <= winterpeil <= {_max}"
                error_list.append(CsvError(csv_row=index, pgid=pgid, error_msg=msg))

        # check 5: col_startdatum < col_einddatum
        mask_error = self.df[self.col_startdatum] >= self.df[self.col_einddatum]
        for index, row in self.df[mask_error].iterrows():
            pgid = row[self.col_pgid]
            error_list.append(CsvError(csv_row=index, pgid=pgid, error_msg="start < einddatum"))

        # check 6: subsequent rows of the same pgid must connect (no gap, and no overlap)
        default_msg = "subsequent rows of the same pgid must connect (no gap, and no overlap)"
        for pgid, df_pgid in self.df.groupby(by=self.col_pgid):
            df_sorted_by_start = df_pgid.sort_values(by=self.col_startdatum)
            previous_end = None
            for row_index, row in df_sorted_by_start.iterrows():
                if not previous_end:
                    previous_end = row[self.col_einddatum]
                    continue
                current_start = row[self.col_startdatum]
                current_start_is_ok = current_start == previous_end
                if not current_start_is_ok:
                    msg = (
                        f"{default_msg}: {self.col_pgid}={pgid}, row={row_index}, {self.col_startdatum}="
                        f"{current_start}, previous_end={previous_end}"
                    )
                    error_list.append(CsvError(csv_row=row_index, pgid=pgid, error_msg=msg))
                previous_end = row[self.col_einddatum]

        # create feedback csv
        error_dict = {}
        for error in error_list:
            existing_error = error_dict.get(error.csv_row, "")
            error_dict[error.csv_row] = f"{existing_error} | {error.error_msg}" if existing_error else error.error_msg
        df_error = self.df.copy()
        df_error["error"] = pd.Series(error_dict)
        df_error_path = self.output_dir / "csv_with_errors.csv"
        logger.info(f"creating {df_error_path}")
        df_error.to_csv(path_or_buf=df_error_path, sep=",", index=False)

        # remove all pgids that have 1 or more errors
        index_errors = sorted(set([x.pgid for x in error_list]))
        mask_pgid_error = self._df[self.col_pgid].isin(index_errors)
        nr_pgid_with_error = len(index_errors)
        nr_rows_with_error = sum(mask_pgid_error)
        if nr_pgid_with_error or nr_rows_with_error:
            logger.warning(f"found {nr_pgid_with_error} pgid with an error, and {nr_rows_with_error} with an error")
            logger.warning(f"deleting {nr_rows_with_error} rows")
        else:
            logger.info("no errors found! :)")
        self._df = self._df[~mask_pgid_error]

        # ensure df is sorted
        self._df = self._df.sort_values([self.col_pgid, self.col_startdatum], ascending=[True, True])

    @staticmethod
    def _add_xml_first_rows(xml_file):
        xml_file.write('<?xml version="1.0" encoding="UTF-8" ?>\n')
        xml_file.write(
            '<TimeSeries xmlns="http://www.wldelft.nl/fews/PI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_timeseriesextended.xsd" version="1.2">\n'  # noqa
        )
        xml_file.write(f"{TAB}<timeZone>1.0</timeZone>\n")
        return xml_file

    @staticmethod
    def _add_xml_last_rows(xml_file):
        xml_file.write("</TimeSeries>\n")
        return xml_file

    @staticmethod
    def _add_xml_series(xml_file, df_pgid: pd.DataFrame, _func):
        """Add one xml series build from one or more csv rows"""
        xml_builder = None
        first_index = min(df_pgid.index)
        last_index = max(df_pgid.index)
        for index, row in df_pgid.iterrows():
            is_first_pgid_csv_row = index == first_index
            is_last_pgid_csv_row = index == last_index
            xml_builder = XmlSeriesBuilder(
                xml_file=xml_file,
                is_first_pgid_csv_row=is_first_pgid_csv_row,
                is_last_pgid_csv_row=is_last_pgid_csv_row,
                df_pgid_row=row,
            )
            xml_builder_method = getattr(xml_builder, _func.__name__)
            xml_file = xml_builder_method()
        return xml_builder.xml_file

    def _create_xml(
        self, xml_path: Path, create_small_xml: bool = False, create_large_xml: bool = True
    ) -> Tuple[Optional[Path], Optional[Path]]:
        if not create_small_xml and not create_large_xml:
            logger.warning("skip creating xmls as create_small_xml=False, create_large_xml=False")

        assert xml_path.suffix == ".xml"

        xml_large_file = None
        xml_large_file_path = None
        if create_large_xml:
            xml_large_file_path = xml_path
            xml_large_file = open(xml_large_file_path.as_posix(), mode="w")
            xml_large_file = self._add_xml_first_rows(xml_file=xml_large_file)

        xml_small_file = None
        xml_small_file_path = None
        if create_small_xml:
            xml_small_file_path = xml_path.parent / f"{xml_path.stem}_test_sample{xml_path.suffix}"
            logger.info("creating also a small test sample (.xml)")
            xml_small_file = open(xml_small_file_path.as_posix(), mode="w")
            xml_small_file = self._add_xml_first_rows(xml_file=xml_small_file)

        df_grouped_by_pgid = self.df.groupby(by=self.col_pgid)
        nr_to_do = len(df_grouped_by_pgid)
        xml_small_file_max_index = int(nr_to_do / 50)  # use ~2% of all data

        progress = 0
        for index, (pgid, df_pgid) in enumerate(df_grouped_by_pgid):
            new_progress = get_progress(iteration_nr=index, nr_to_do=nr_to_do)
            if new_progress != progress:
                logger.info(f"build .xml progress = {get_progress(iteration_nr=index, nr_to_do=nr_to_do)}%")
                progress = new_progress
            for _func in (
                XmlSeriesBuilder.add_series_peilbesluitpeil,
                XmlSeriesBuilder.add_series_eerste_ondergrens,
                XmlSeriesBuilder.add_series_tweede_ondergrens,
                XmlSeriesBuilder.add_series_eerste_bovengrens,
                XmlSeriesBuilder.add_series_tweede_bovengrens,
            ):
                if create_small_xml and index < xml_small_file_max_index:
                    xml_small_file = self._add_xml_series(xml_file=xml_small_file, df_pgid=df_pgid, _func=_func)
                if create_large_xml:
                    xml_large_file = self._add_xml_series(xml_file=xml_large_file, df_pgid=df_pgid, _func=_func)

        if create_small_xml:
            xml_small_file = self._add_xml_last_rows(xml_file=xml_small_file)
            xml_small_file.close()
        if create_large_xml:
            xml_large_file = self._add_xml_last_rows(xml_file=xml_large_file)
            xml_large_file.close()

        return xml_small_file_path, xml_large_file_path

    def run(self):
        csv_orig = self.output_dir / "csv_orig.csv"
        logger.info(f"creating {csv_orig}")
        self.df.to_csv(path_or_buf=csv_orig, sep=",", index=False)

        # create csv that was used as input for xml
        self.validate_df()
        csv_source_path = self.output_dir / "csv_without_errors.csv"
        logger.info(f"creating {csv_source_path}")
        self.df.to_csv(path_or_buf=csv_source_path, sep=",", index=False)

        # create .xml
        if not constants.CREATE_XML:
            logger.info("skip creating xml")
            return
        xml_path = self.output_dir / "PeilbesluitPi.xml"
        logger.info(f"creating {xml_path}")
        _, _ = self._create_xml(xml_path=xml_path, create_small_xml=True)
