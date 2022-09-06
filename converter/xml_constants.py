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


#         In WIS 7.0 Productie one can see that peilbesluit graphs (grafieken > ster > peilbesluitevaluatie > marges aanzetten (knopje rechtsboven)).
#         The graphs shows a waterlevel line and 5 "block" lines:
#             1) peilbesluitpeil [mNAP] has 4 periods:
#                     1) eind_winter - begin_zomer:   level = avg(zomer_peil, winter_peil)
#                     2) begin_zomer - eind_zomer:    level = zomerpeil
#                     3) eind_zomer - begin_winter:   level = avg(zomer_peil, winter_peil)
#                     4) begin_winter - eind_winter:  level = winterpeil
#             2) and 3) marge eerste en tweede bovengrens [mNAP] has 2 periods:
#                     1) eind_winter - begin_winter
#                     2) begin_winter - eind_winter
#             4) and 5) marge eerste en tweede ondergrens [mNAP] has 2 periods:
#                     1) begin_zomer - eind_zomer
#                     2) eind_zomer - begin_zomer


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
