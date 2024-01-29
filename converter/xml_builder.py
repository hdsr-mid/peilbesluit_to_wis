from converter import constants
from converter import timeseries_builder
from converter.constants import ColumnNameDtypeConstants
from converter.constants import TAB
from converter.constants import XmlConstants
from datetime import datetime

import pandas as pd


class XmlSeriesBuilder(ColumnNameDtypeConstants):

    """
    Below the first three rows of the input csv are shown:

    pgid    startdatum	einddatum   eind_winter begin_zomer eind_zomer  begin_winter    zomerpeil   winterpeil  2e_marge_onder  1e_marge_onder  1e_marge_boven  2e_marge_boven  # noqa
    --------------------------------------------------------------------------------------------------------------------------------------------------------------------------  # noqa
    PG0566  20190101    20201023	01-04	    01-05       01-09	    01-10           1.5         1.25        25              10	            10	            25              # noqa
    PG0566  20201023	20210610	01-04	    01-05       01-09	    01-10           915         915	        25              50.5            50.5	        25              # noqa
    PG0064  20190101	20190717	01-04	    01-05	    01-09       01-10           1.65	    1.45        25              10              10              25              # noqa

    In WIS 7.0 Productie one can see that peilbesluit graphs (grafieken > ster > peilbesluitevaluatie > marges aanzetten (knopje rechtsboven)).
    The graphs shows a waterlevel line and 5 "block" lines:
        1) peilbesluitpeil [mNAP] has 4 periods:
                1) eind_winter - begin_zomer:   level = avg(zomer_peil, winter_peil)
                2) begin_zomer - eind_zomer:    level = zomerpeil
                3) eind_zomer - begin_winter:   level = avg(zomer_peil, winter_peil)
                4) begin_winter - eind_winter:  level = winterpeil
        2) and 3) marge eerste en tweede bovengrens [mNAP] has 2 periods:
                1) eind_winter - begin_winter:  level = zomerpeil + marge
                2) begin_winter - eind_winter:  level = winterpeil + marge
        4) and 5) marge eerste en tweede ondergrens [mNAP] has 2 periods:
                1) begin_zomer - eind_zomer:    level = zomer_peil = marge
                2) eind_zomer - begin_zomer:    level = winter_peil = marge

    All csv rows with the same pgid (can be 1 row) result in multiple xml series, each with an own header.
    We see the xml result of the first csv two rows (the share the same pgid):
    """

    def __init__(self, xml_file, is_first_pgid_csv_row: bool, is_last_pgid_csv_row: bool, df_pgid_row: pd.Series):
        self.xml_file = xml_file
        self.is_first_pgid_csv_row = is_first_pgid_csv_row
        self.is_last_pgid_csv_row = is_last_pgid_csv_row
        self.pgid = str(df_pgid_row[self.col_pgid])
        self.startdatum = df_pgid_row[self.col_startdatum]
        self.einddatum = df_pgid_row[self.col_einddatum]
        self.eind_winter = str(df_pgid_row[self.col_eind_winter])
        self.begin_zomer = str(df_pgid_row[self.col_begin_zomer])
        self.eind_zomer = str(df_pgid_row[self.col_eind_zomer])
        self.begin_winter = str(df_pgid_row[self.col_begin_winter])
        self.zomerpeil = float(df_pgid_row[self.col_zomerpeil])
        self.winterpeil = float(df_pgid_row[self.col_winterpeil])
        self._2e_marge_onder = float(df_pgid_row[self.col_2e_marge_onder])
        self._1e_marge_onder = float(df_pgid_row[self.col_1e_marge_onder])
        self._1e_marge_boven = float(df_pgid_row[self.col_1e_marge_boven])
        self._2e_marge_boven = float(df_pgid_row[self.col_2e_marge_boven])

    @staticmethod
    def add_xml_series(xml_file):
        return xml_file

    @staticmethod
    def get_xml_datestring(value) -> str:
        datetime_obj = None
        if isinstance(value, str):
            try:
                datetime_obj = datetime.strptime(value, constants.DateFormats.yyyymmdd.value)
            except Exception:  # noqa
                datetime_obj = datetime.strptime(value, constants.DateFormats.yyyy_mm_dd.value)
        elif isinstance(value, datetime):
            datetime_obj = value
        return datetime_obj.strftime(constants.DateFormats.yyyy_mm_dd.value)

    def add_end_of_events(self):
        self.xml_file.write(f"{TAB}</series>\n")  # noqa

    def add_header(self, timeseries_constants):
        startdate_str = self.get_xml_datestring(value=self.startdatum)
        enddate_str = self.get_xml_datestring(value=self.einddatum)
        self.xml_file.write(f"{TAB*1}<series>\n")
        self.xml_file.write(f"{TAB*2}<header>\n")
        self.xml_file.write(f"{TAB*3}<type>instantaneous</type>\n")
        self.xml_file.write(f"{TAB*3}<locationId>{self.pgid}</locationId>\n")
        self.xml_file.write(f"{TAB*3}<parameterId>{timeseries_constants.parameter_id}</parameterId>\n")
        self.xml_file.write(f'{TAB*3}<timeStep unit="nonequidistant"/>\n')
        self.xml_file.write(f'{TAB*3}<startDate date="{startdate_str}" time="00:00:00"></startDate>\n')
        self.xml_file.write(f'{TAB*3}<endDate date="{enddate_str}" time="00:00:00"></endDate>\n')
        self.xml_file.write(f"{TAB*3}<missVal>-999.99</missVal>\n")
        self.xml_file.write(f"{TAB*3}<longName>{timeseries_constants.longname}</longName>\n")
        self.xml_file.write(f"{TAB*3}<units>{timeseries_constants.units}</units>\n")
        self.xml_file.write(f"{TAB*3}<sourceOrganisation></sourceOrganisation>\n")
        self.xml_file.write(f"{TAB*3}<sourceSystem>tijdreeks FEWS-PI.xls</sourceSystem>\n")
        self.xml_file.write(f"{TAB*3}<fileDescription></fileDescription>\n")
        self.xml_file.write(f"{TAB*3}<region></region>\n")
        self.xml_file.write(f"{TAB*2}</header>\n")

    def add_series_peilbesluitpeil(self):
        timeseries_constants = XmlConstants.peilbesluitpeil
        if self.is_first_pgid_csv_row:
            self.add_header(timeseries_constants=timeseries_constants)

        ts_builder = timeseries_builder.PeilbesluitPeil(
            # baseclass arguments
            pgid=self.pgid,
            startdatum=self.startdatum,
            einddatum=self.einddatum,
            zomerpeil=self.zomerpeil,
            winterpeil=self.winterpeil,
            # subclass arguments
            eind_winter=self.eind_winter,
            begin_zomer=self.begin_zomer,
            eind_zomer=self.eind_zomer,
            begin_winter=self.begin_winter,
        )
        series_data = ts_builder.get_series(
            is_first_pgid_csv_row=self.is_first_pgid_csv_row, is_last_pgid_csv_row=self.is_last_pgid_csv_row
        )
        for series in series_data:
            date, level = series
            date_string = date.strftime(constants.DateFormats.yyyy_mm_dd.value)
            level_str = f"{level:.2f}"  # ensure two decimals
            xml_line = f'{TAB*2}<event date="{date_string}" time="00:00:00" value="{level_str}" flag="0"/>\n'
            self.xml_file.write(xml_line)

        if self.is_last_pgid_csv_row:
            self.add_end_of_events()

        return self.xml_file

    def add_series_eerste_ondergrens(self):
        timeseries_constants = XmlConstants.eerste_ondergrens

        if self.is_first_pgid_csv_row:
            self.add_header(timeseries_constants=timeseries_constants)

        ts_builder = timeseries_builder.Ondergrens(
            # baseclass arguments
            pgid=self.pgid,
            startdatum=self.startdatum,
            einddatum=self.einddatum,
            zomerpeil=self.zomerpeil,
            winterpeil=self.winterpeil,
            # subclass arguments
            begin_zomer=self.begin_zomer,
            eind_zomer=self.eind_zomer,
            marge=self._1e_marge_onder,
        )
        series_data = ts_builder.get_series(
            is_first_pgid_csv_row=self.is_first_pgid_csv_row, is_last_pgid_csv_row=self.is_last_pgid_csv_row
        )
        for series in series_data:
            date, level = series
            date_string = date.strftime(constants.DateFormats.yyyy_mm_dd.value)
            level_str = f"{level:.2f}"  # ensure two decimals
            xml_line = f'{TAB*2}<event date="{date_string}" time="00:00:00" value="{level_str}" flag="0"/>\n'
            self.xml_file.write(xml_line)

        if self.is_last_pgid_csv_row:
            self.add_end_of_events()

        return self.xml_file

    def add_series_tweede_ondergrens(self):
        timeseries_constants = XmlConstants.tweede_ondergrens

        if self.is_first_pgid_csv_row:
            self.add_header(timeseries_constants=timeseries_constants)

        ts_builder = timeseries_builder.Ondergrens(
            # baseclass arguments
            pgid=self.pgid,
            startdatum=self.startdatum,
            einddatum=self.einddatum,
            zomerpeil=self.zomerpeil,
            winterpeil=self.winterpeil,
            # subclass arguments
            begin_zomer=self.begin_zomer,
            eind_zomer=self.eind_zomer,
            marge=self._2e_marge_onder,
        )
        series_data = ts_builder.get_series(
            is_first_pgid_csv_row=self.is_first_pgid_csv_row, is_last_pgid_csv_row=self.is_last_pgid_csv_row
        )
        for series in series_data:
            date, level = series
            date_string = date.strftime(constants.DateFormats.yyyy_mm_dd.value)
            level_str = f"{level:.2f}"  # ensure two decimals
            xml_line = f'{TAB*2}<event date="{date_string}" time="00:00:00" value="{level_str}" flag="0"/>\n'
            self.xml_file.write(xml_line)

        if self.is_last_pgid_csv_row:
            self.add_end_of_events()

        return self.xml_file

    def add_series_eerste_bovengrens(self):
        timeseries_constants = XmlConstants.eerste_bovengrens

        if self.is_first_pgid_csv_row:
            self.add_header(timeseries_constants=timeseries_constants)

        ts_builder = timeseries_builder.Bovengrens(
            # baseclass arguments
            pgid=self.pgid,
            startdatum=self.startdatum,
            einddatum=self.einddatum,
            zomerpeil=self.zomerpeil,
            winterpeil=self.winterpeil,
            # subclass arguments
            eind_winter=self.eind_winter,
            begin_winter=self.begin_winter,
            marge=self._1e_marge_boven,
        )
        series_data = ts_builder.get_series(
            is_first_pgid_csv_row=self.is_first_pgid_csv_row, is_last_pgid_csv_row=self.is_last_pgid_csv_row
        )

        for series in series_data:
            date, level = series
            date_string = date.strftime(constants.DateFormats.yyyy_mm_dd.value)
            level_str = f"{level:.2f}"  # ensure two decimals
            xml_line = f'{TAB*2}<event date="{date_string}" time="00:00:00" value="{level_str}" flag="0"/>\n'
            self.xml_file.write(xml_line)

        if self.is_last_pgid_csv_row:
            self.add_end_of_events()

        return self.xml_file

    def add_series_tweede_bovengrens(self):
        timeseries_constants = XmlConstants.tweede_bovengrens

        if self.is_first_pgid_csv_row:
            self.add_header(timeseries_constants=timeseries_constants)

        ts_builder = timeseries_builder.Bovengrens(
            # baseclass arguments
            pgid=self.pgid,
            startdatum=self.startdatum,
            einddatum=self.einddatum,
            zomerpeil=self.zomerpeil,
            winterpeil=self.winterpeil,
            # subclass arguments
            eind_winter=self.eind_winter,
            begin_winter=self.begin_winter,
            marge=self._2e_marge_boven,
        )
        series_data = ts_builder.get_series(
            is_first_pgid_csv_row=self.is_first_pgid_csv_row, is_last_pgid_csv_row=self.is_last_pgid_csv_row
        )
        for series in series_data:
            date, level = series
            date_string = date.strftime(constants.DateFormats.yyyy_mm_dd.value)
            level_str = f"{level:.2f}"  # ensure two decimals
            xml_line = f'{TAB*2}<event date="{date_string}" time="00:00:00" value="{level_str}" flag="0"/>\n'
            self.xml_file.write(xml_line)

        if self.is_last_pgid_csv_row:
            self.add_end_of_events()

        return self.xml_file
