from datetime import datetime


class ConstantPeriod:
    def __init__(self, start: str, end: str, level: float):
        self.start = start
        self.end = end
        self.level = level
        self.start_month_int = int(start.split("-")[0])
        self.start_day_int = int(start.split("-")[1])
        self.end_month_int = int(end.split("-")[0])
        self.end_day_int = int(end.split("-")[1])


class BuilderBase:
    def __init__(
        self,
        pgid: str,
        startdatum: datetime,
        einddatum: datetime,
        zomerpeil: float,
        winterpeil: float,
    ):
        self.cls_name = self.__class__.__name__
        self.pgid = pgid
        self.startdatum = startdatum
        self.einddatum = einddatum
        self.zomerpeil = zomerpeil
        self.winterpeil = winterpeil
        self._periods_mapper = None
        self._validate_periods()

    @property
    def periods(self) -> list:
        """
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
        """
        raise NotImplementedError

    @property
    def periods_mapper(self) -> dict:
        """This property is almost equal to property periods, but now in dictionary to speed up searching)."""
        if self._periods_mapper is not None:
            return self._periods_mapper
        self._periods_mapper = {
            (p.start_month_int, p.start_day_int, p.end_month_int, p.end_day_int): p for p in self.periods
        }
        return self._periods_mapper

    @staticmethod
    def month_day(datestring: str):
        month = int(datestring.split("-")[0])
        day = int(datestring.split("-")[1])
        return month, day

    def _validate_periods(self) -> None:
        default_msg = f"{self.cls_name} has invalid (overlap/gap) periods:"
        assert all([isinstance(x, ConstantPeriod) for x in self.periods])
        starts = [x.start for x in self.periods]
        ends = [x.end for x in self.periods]
        assert len(starts) == len(set(starts)), f"{default_msg}: period startdates {starts} must be unique"
        assert len(starts) == len(set(starts)), f"{default_msg}: period enddates {ends} must be unique"
        first_start = starts[0]
        last_end = None
        previous_end = None
        for period in self.periods:
            current_start = period.start
            current_end = period.end
            assert current_start, f"{default_msg}: at least one period has an empty start"
            assert current_end, f"{default_msg}: at least one period has an empty end"
            assert isinstance(period.level, float)
            if previous_end and current_start != previous_end:
                raise AssertionError(f"{default_msg} startdate {current_start} must be previous_end {previous_end}")
            previous_end = current_end
            last_end = current_end
        assert last_end == first_start, f"{default_msg}: last_end {last_end} must be first_start {first_start}"

    def create_series(self):
        startdatum_level = self.get_level_in_between_date(month=self.startdatum.month, day=self.startdatum.day)
        einddatum_level = self.get_level_in_between_date(month=self.einddatum.month, day=self.einddatum.day)

    def get_level_in_between_date(self, month: int, day: int):
        current_dummy_year = 2000
        dummy_in_between_date = datetime(year=current_dummy_year, month=month, day=day)
        for index, period in enumerate(self.periods):
            is_last_element = index == len(self.periods) - 1
            start_datetime_obj = datetime(
                year=current_dummy_year, month=period.start_month_int, day=period.start_day_int
            )
            if is_last_element:
                end_datetime_obj = datetime(
                    year=current_dummy_year + 1, month=period.end_month_int, day=period.end_day_int
                )
            else:
                end_datetime_obj = datetime(year=current_dummy_year, month=period.end_month_int, day=period.end_day_int)
            if start_datetime_obj <= dummy_in_between_date <= end_datetime_obj:
                return period.level
        raise AssertionError("code error, this should not happen")


class PeilbesluitPeil(BuilderBase):
    def __init__(self, eind_winter: str, begin_zomer: str, eind_zomer: str, begin_winter: str, **kwargs):
        assert [x for x in (eind_winter, begin_winter, eind_zomer, begin_winter)]
        self.eind_winter = eind_winter
        self.begin_zomer = begin_zomer
        self.eind_zomer = eind_zomer
        self.begin_winter = begin_winter
        super().__init__(**kwargs)

    @property
    def periods(self) -> list:
        p1 = ConstantPeriod(start=self.eind_winter, end=self.begin_zomer, level=(self.zomerpeil + self.winterpeil) / 2)
        p2 = ConstantPeriod(start=self.begin_zomer, end=self.eind_zomer, level=self.zomerpeil)
        p3 = ConstantPeriod(start=self.eind_zomer, end=self.begin_winter, level=(self.zomerpeil + self.winterpeil) / 2)
        p4 = ConstantPeriod(start=self.begin_winter, end=self.eind_winter, level=self.winterpeil)
        return [p1, p2, p3, p4]
