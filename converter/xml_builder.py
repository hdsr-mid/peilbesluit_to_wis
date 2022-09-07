from converter import constants
from converter.timeseries_builder import PeilbesluitPeil
from converter.xml_constants import XmlConstants
from datetime import datetime


class XmlSeriesBuilder:

    tab = "    "

    def __init__(self, xml_file, is_first_pgid_csv_row: bool, is_last_pgid_csv_row: bool, **kwargs):
        self.xml_file = xml_file
        self.is_first_pgid_csv_row = is_first_pgid_csv_row
        self.is_last_pgid_csv_row = is_last_pgid_csv_row
        self.pgid = str(kwargs.pop("pgid"))
        self.startdatum = datetime.strptime(kwargs.pop("startdatum"), "%Y%m%d")
        self.einddatum = datetime.strptime(kwargs.pop("einddatum"), "%Y%m%d")
        self.eind_winter = str(kwargs.pop("eind_winter"))
        self.begin_zomer = str(kwargs.pop("begin_zomer"))
        self.eind_zomer = str(kwargs.pop("eind_zomer"))
        self.begin_winter = str(kwargs.pop("begin_winter"))
        self.zomerpeil = float(kwargs.pop("zomerpeil"))
        self.winterpeil = float(kwargs.pop("winterpeil"))
        self._2e_marge_onder = float(kwargs.pop("2e_marge_onder"))
        self._1e_marge_onder = float(kwargs.pop("1e_marge_onder"))
        self._1e_marge_boven = float(kwargs.pop("1e_marge_boven"))
        self._2e_marge_boven = float(kwargs.pop("2e_marge_boven"))

    @staticmethod
    def add_xml_series(xml_file):
        return xml_file

    @staticmethod
    def get_xml_datestring(value) -> str:
        datetime_obj = None
        if isinstance(value, str):
            try:
                datetime_obj = datetime.strptime(value, "%Y%m%d")
            except Exception:  # noqa
                datetime_obj = datetime.strptime(value, "%Y-%m-%d")
        elif isinstance(value, datetime):
            datetime_obj = value
        return datetime_obj.strftime("%Y%m%d")

    @staticmethod
    def get_month_day(value: str):
        datetime_obj = None
        if isinstance(value, str):
            for datestring_format in ("%m-%d", "%Y%m%d", "%Y-%m-%d"):
                try:
                    datetime_obj = datetime.strptime(value, datestring_format)
                except Exception:  # noqa
                    pass
            assert datetime_obj
        elif isinstance(value, datetime):
            datetime_obj = value
        return datetime_obj.month, datetime_obj.day

    def add_header(self, timeseries_constants):
        """
        <series>
            <header>
                <type>instantaneous</type>
                <locationId>PG0566</locationId>
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
        """
        self.xml_file.write(f"{self.tab}<series>\n")  # noqa
        self.xml_file.write(f"{self.tab*2}<header>\n")  # noqa
        self.xml_file.write(f"{self.tab*3}<type>instantaneous</type>\n")  # noqa
        self.xml_file.write(f"{self.tab*3}<locationId>{self.pgid}</locationId>\n")
        self.xml_file.write(f"{self.tab*3}<parameterId>{timeseries_constants.parameter_id}</parameterId>\n")
        self.xml_file.write(f'{self.tab*3}<timeStep unit="nonequidistant"/>\n')
        self.xml_file.write(
            f'{self.tab*3}<startDate date="{self.get_xml_datestring(value=self.startdatum)}" time="00:00:00"></startDate>\n'
        )
        self.xml_file.write(
            f'{self.tab*3}<endDate date="{self.get_xml_datestring(value=self.einddatum)}" time="00:00:00"></endDate>\n'
        )
        self.xml_file.write(f"{self.tab*3}<missVal>-999.99</missVal>\n")
        self.xml_file.write(f"{self.tab*3}<longName>{timeseries_constants.longname}</longName>\n")
        self.xml_file.write(f"{self.tab*3}<units>{timeseries_constants.units}</units>\n")
        self.xml_file.write(f"{self.tab*3}<sourceOrganisation></sourceOrganisation>\n")
        self.xml_file.write(f"{self.tab*3}<sourceSystem>tijdreeks FEWS-PI.xls</sourceSystem>\n")
        self.xml_file.write(f"{self.tab*3}<fileDescription></fileDescription>\n")
        self.xml_file.write(f"{self.tab*3}<region></region>\n")
        self.xml_file.write(f"{self.tab*2}</header>\n")

    def add_series_startdate(self):
        print(1)

    def create_series_peilbesluit(self):
        print(1)

    def _get_timeseries_value(self, month, day):
        """
        Below the first three rows of the input csv are shown:

        pgid    startdatum	einddatum   eind_winter begin_zomer eind_zomer  begin_winter    zomerpeil   winterpeil  2e_marge_onder  1e_marge_onder  1e_marge_boven  2e_marge_boven
        --------------------------------------------------------------------------------------------------------------------------------------------------------------------------
        PG0566  20190101    20201023	01-04	    01-05       01-09	    01-10           1.5         1.25        25              10	            10	            25
        PG0566  20201023	20210610	01-04	    01-05       01-09	    01-10           915         915	        25              50.5            50.5	        25
        PG0064  20190101	20190717	01-04	    01-05	    01-09       01-10           1.65	    1.45        25              10              10              25

        In WIS 7.0 Productie one can see that peilbesluit graphs (grafieken > ster > peilbesluitevaluatie > marges aanzetten (knopje rechtsboven)).
        The graphs shows a waterlevel line and 5 "block" lines:
            1) peilbesluitpeil [mNAP] has 4 periods:
                    1) eind_winter - begin_zomer:   level = avg(zomer_peil, winter_peil)
                    2) begin_zomer - eind_zomer:    level = zomerpeil
                    3) eind_zomer - begin_winter:   level = avg(zomer_peil, winter_peil)
                    4) begin_winter - eind_winter:  level = winterpeil
            2) and 3) marge eerste en tweede bovengrens [mNAP] has 2 periods:
                    1) eind_winter - begin_winter
                    2) begin_winter - eind_winter
            4) and 5) marge eerste en tweede ondergrens [mNAP] has 2 periods:
                    1) begin_zomer - eind_zomer
                    2) eind_zomer - begin_zomer

        All csv rows with the same pgid (can be 1 row) result in multiple xml series, each with an own header.
        We see the xml result of the first csv two rows (the share the same pgid):
        """
        print(1)

    def add_series_peilbesluitpeil(self):
        """
        <?xml version="1.0" encoding="UTF-8" ?>
        <TimeSeries xmlns="http://www.wldelft.nl/fews/PI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_timeseriesextended.xsd" version="1.2">
            <timeZone>1.0</timeZone>
            <series>
                <header>
                    <type>instantaneous</type>
                    <locationId>PG0566</locationId>
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
                <event date="1990-01-01" time="00:00:00" value="0.80" flag="0"/>            # startdate
                <event date="1990-04-01" time="00:00:00" value="0.95" flag="0"/>            # eind_winter
                <event date="1990-05-01" time="00:00:00" value="1.10" flag="0"/>            # begin_zomer
                <event date="1990-09-01" time="00:00:00" value="0.95" flag="0"/>            # eind_zomer
                <event date="1990-10-01" time="00:00:00" value="0.80" flag="0"/>            # begin_winter
                <event date="1991-04-01" time="00:00:00" value="0.95" flag="0"/>            # eind_winter (!)
                ...
                <event date="2023-05-01" time="00:00:00" value="1.10" flag="0"/>            # begin_zomer
                <event date="2023-09-01" time="00:00:00" value="0.95" flag="0"/>            # eind_zomer
                <event date="2023-10-01" time="00:00:00" value="0.80" flag="0"/>            # begin_winter
                <event date="2023-10-23" time="00:00:00" value="0.80" flag="0"/>            # <-- enddate
            </series>
            <series>
            ...
            </series>
        </TimeSeries>

        Peilbesluit timeseries is a block line with 4 levels (for 4 periods):
            1) eind_winter - begin_zomer:   level = avg(zomer_peil, winter_peil)
            2) begin_zomer - eind_zomer:    level = zomerpeil
            3) eind_zomer - begin_winter:   level = avg(zomer_peil, winter_peil)
            4) begin_winter - eind_winter:  level = winterpeil

        """
        timeseries_constants = XmlConstants.peilbesluitpeil
        if self.is_first_pgid_csv_row:
            self.add_header(timeseries_constants=timeseries_constants)

        ts_builder = PeilbesluitPeil(
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
        series = ts_builder.create_series()

        print(1)

    def add_series_eerste_ondergrens(self):
        if self.is_first_pgid_csv_row:
            print(1)
        timeseries_constants = XmlConstants.eerste_ondergrens
        print(1)

    def add_series_tweede_ondergrens(self):
        if self.is_first_pgid_csv_row:
            print(1)
        timeseries_constants = XmlConstants.tweede_ondergrens
        print(1)

    def add_series_eerste_bovengrens(self):
        timeseries_constants = XmlConstants.eerste_bovengrens
        print(1)

    def add_series_tweede_bovengrens(self):
        timeseries_constants = XmlConstants.tweede_bovengrens
        print(1)

    def create_and_save_xml(self):

        """
        <?xml version="1.0" encoding="UTF-8" ?>
        <TimeSeries xmlns="http://www.wldelft.nl/fews/PI" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xsi:schemaLocation="http://www.wldelft.nl/fews/PI http://fews.wldelft.nl/schemas/version1.0/pi-schemas/pi_timeseriesextended.xsd" version="1.2">
            <timeZone>1.0</timeZone>
            <series>
                <header>
                    <type>instantaneous</type>
                    <locationId>PG0566</locationId>
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
                <event date="1990-01-01" time="00:00:00" value="0.80" flag="0"/>            # startdate
                <event date="1990-04-01" time="00:00:00" value="0.95" flag="0"/>            # eind_winter
                <event date="1990-05-01" time="00:00:00" value="1.10" flag="0"/>            # begin_zomer
                <event date="1990-09-01" time="00:00:00" value="0.95" flag="0"/>            # eind_zomer
                <event date="1990-10-01" time="00:00:00" value="0.80" flag="0"/>            # begin_winter
                <event date="1991-04-01" time="00:00:00" value="0.95" flag="0"/>            # eind_winter (!)
                ...
                <event date="2023-05-01" time="00:00:00" value="1.10" flag="0"/>            # begin_zomer
                <event date="2023-09-01" time="00:00:00" value="0.95" flag="0"/>            # eind_zomer
                <event date="2023-10-01" time="00:00:00" value="0.80" flag="0"/>            # begin_winter
                <event date="2023-10-23" time="00:00:00" value="0.80" flag="0"/>            # <-- enddate
            </series>
            <series>
            ...
            </series>
        </TimeSeries>

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

        """

    def add_header_to_xml(self, xml_file, pgid: str, parameter_id: str, startdate: datetime, enddate: datetime) -> str:
        """
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
        """
        xml_file.write(f"   <header>\n")
        xml_file.write(f"       <type>instantaneous</type>\n")
        xml_file.write(f"           <locationId>{pgid}</locationId>\n")
        xml_file.write(f"			<parameterId>{parameter_id}</parameterId>\n")
        xml_file.write(f'			<timeStep unit="nonequidistant"/>\n')
        xml_file.write(f'		    <startDate date="{startdate.strftime("%Y-%m-%d")}" time="00:00:00"></startDate>\n')
        xml_file.write(f'		    <endDate date="{enddate.strftime("%Y-%m-%d")}" time="00:00:00"></endDate>\n')
        xml_file.write(f"			<missVal>-999.99</missVal>\n")
        xml_file.write(f'           <longName>Peilbesluitpeil"</longName>\n')
        xml_file.write(f"			<units>m</units>\n")
        xml_file.write(f"			<sourceOrganisation></sourceOrganisation>\n")
        xml_file.write(f"			<sourceSystem>tijdreeks FEWS-PI.xls</sourceSystem>\n")
        xml_file.write(f"			<fileDescription></fileDescription>\n")
        xml_file.write(f"			<region></region>\n")
        xml_file.write(f"		</header>\n")
        return xml_file
