from converter import constants
from converter.constants import ColumnNameDtypeConstants
from converter.constants import TAB
from converter.utils import DatesColumns
from converter.utils import get_progress
from converter.xml_builder import XmlSeriesBuilder
from datetime import datetime
from hdsr_wis_config_reader.utils import PdReadFlexibleCsv
from pathlib import Path
from typing import Tuple

import logging
import pandas as pd


logger = logging.getLogger(__name__)


class ConvertCsvToXml(ColumnNameDtypeConstants):
    def __init__(self, orig_csv_path: Path):
        self.orig_csv_path = orig_csv_path
        self._df = None
        self._csv_rows_no_error = None
        self._output_xml_path = None
        self.datecolumn_start = DatesColumns(column_name=self.col_startdatum, date_format="%Y%m%d", errors="raise")
        self.datecolumn_eind = DatesColumns(column_name=self.col_einddatum, date_format="%Y%m%d", errors="raise")

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

    @staticmethod
    def get_month_day_from_string(datestr_m_d: str) -> Tuple[int, int]:
        fmt = constants.DateFormats.dd_mm.value
        try:
            date_obj = pd.to_datetime(datestr_m_d, format=fmt)
        except Exception:
            raise AssertionError(f"we expected date format '{fmt}' so e.g. '01-04' (in other words: April 1)")
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
        wrong_peil_row_indices = []
        wrong_peil_pgids = []
        wrong_marge_row_indices = []
        wrong_marge_pgids = []
        for index, row in self.df.iterrows():

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
                    raise AssertionError(msg)
            except KeyError:
                wrong_marge_row_indices.append(index)
                wrong_marge_pgids.append(index)

            # check 3: validate boven marges per row
            _min = constants.MIN_ALLOW_UPPER_MARGIN_CM
            _max = constants.MAX_ALLOW_UPPER_MARGIN_CM
            try:
                boven_marges_are_ok = _min <= row[self.col_1e_marge_boven] <= row[self.col_2e_marge_boven] <= _max
                if not boven_marges_are_ok:
                    msg = f"invalid boven marges as we expected {_min} <= _1e_marge_boven <= _2e_marge_boven <= {_max}"
                    raise AssertionError(msg)
            except KeyError:
                wrong_marge_row_indices.append(index)
                wrong_marge_pgids.append(index)

            # check 4: check peilen
            _min = constants.MIN_ALLOWED_MNAP
            _max = constants.MAX_ALLOWED_MNAP
            zomerpeil_ok = _min <= row[self.col_zomerpeil] <= _max
            winterpeil_ok = _min <= row[self.col_winterpeil] <= _max
            if not zomerpeil_ok or not winterpeil_ok:
                wrong_peil_row_indices.append(index)
                wrong_peil_pgids.append(row[self.col_pgid])

        wrong_marge_row_indices = sorted(set(wrong_marge_row_indices))  # noqa
        wrong_marge_pgids = sorted(set(wrong_marge_pgids))  # noqa
        if wrong_marge_row_indices:
            logger.warning(f"found {len(wrong_marge_row_indices)} rows with a invalid marge: {wrong_marge_row_indices}")
            # remove all pgids that have 1 or more wrong marge
            mask_wrong_marge_pgids = self._df[self.col_pgid].isin(wrong_marge_pgids)
            logger.warning(f"removing {len(wrong_marge_pgids)} pgid from input")
            self._df = self._df[~mask_wrong_marge_pgids]

        wrong_peil_row_indices = sorted(set(wrong_peil_row_indices))  # noqa
        wrong_peil_pgids = list(set(wrong_peil_pgids))  # noqa
        if wrong_peil_row_indices:
            logger.warning(f"found {len(wrong_peil_row_indices)} rows with a invalid peil: {wrong_peil_row_indices}")
            # remove all pgids that have 1 or more wrong peil
            mask_wrong_peil_pgids = self._df[self.col_pgid].isin(wrong_peil_pgids)
            logger.warning(f"removing {len(wrong_peil_pgids)} pgid from input")
            self._df = self._df[~mask_wrong_peil_pgids]

        # check 5: col_startdatum < col_einddatum
        mask_error = self.df[self.col_startdatum] >= self.df[self.col_einddatum]
        nr_errors = mask_error.sum()
        if nr_errors:
            rows_index = [idx for idx in mask_error.index if mask_error[idx]]  # noqa
            raise AssertionError(f"{self.col_startdatum} < {self.col_einddatum} error in rows {rows_index}")

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
                    raise AssertionError(msg)
                previous_end = row[self.col_einddatum]

        # ensure df is sorted
        self._df = self._df.sort_values([self.col_pgid, self.col_startdatum], ascending=[True, False])

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

    def _create_xml(self, xml_path: Path) -> None:
        xml_file = open(xml_path.as_posix(), mode="w")
        xml_file = self._add_xml_first_rows(xml_file=xml_file)

        df_grouped_by_pgid = self.df.groupby(by=self.col_pgid)
        nr_to_do = len(df_grouped_by_pgid)
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
                xml_file = self._add_xml_series(xml_file=xml_file, df_pgid=df_pgid, _func=_func)
        xml_file = self._add_xml_last_rows(xml_file=xml_file)
        xml_file.close()

    def run(self):
        self.validate_df()
        if not constants.CREATE_XML:
            logger.info("skip creating xml")
            return

        datetime_str_now = datetime.now().strftime("%Y%m%d_%H%M%S")
        csv_source_path = constants.DATA_OUTPUT_DIR / f"PeilbesluitPi_{datetime_str_now}_valid_input_for_xml.csv"
        xml_path = constants.DATA_OUTPUT_DIR / f"PeilbesluitPi_{datetime_str_now}.xml"

        # create csv that was used as input for xml
        self.df.to_csv(path_or_buf=csv_source_path, sep=",", index=False)

        # create .xml
        self._create_xml(xml_path=xml_path)
