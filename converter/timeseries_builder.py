from converter.constants import DateFormats
from datetime import datetime
from datetime import timedelta


class ConstantPeriod:
    def __init__(self, start: str, end: str, level: float):
        self.start = start
        self.end = end
        self.level = level
        self.start_month_int = datetime.strptime(start, DateFormats.dd_mm.value).month
        self.start_day_int = datetime.strptime(start, DateFormats.dd_mm.value).day
        self.end_month_int = datetime.strptime(end, DateFormats.dd_mm.value).month
        self.end_day_int = datetime.strptime(end, DateFormats.dd_mm.value).day

    def __repr__(self):
        return f"start={self.start}, end={self.end}, level={self.level}"


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

    def get_series(self, is_first_pgid_csv_row: bool, is_last_pgid_csv_row: bool) -> list:
        startdatum_period = self.get_period_in_between_date(month=self.startdatum.month, day=self.startdatum.day)
        einddatum_period = self.get_period_in_between_date(month=self.einddatum.month, day=self.einddatum.day)
        series_data = [(self.startdatum, startdatum_period.level)]
        years = [x for x in range(self.startdatum.year, self.einddatum.year)]
        years = sorted(set(years + [self.startdatum.year, self.einddatum.year]))
        for year in years:
            for period in self.periods:
                possible_date = datetime(year=year, month=period.start_month_int, day=period.start_day_int)
                last_date = series_data[-1][0]
                if last_date < possible_date < self.einddatum:
                    series_data.append((possible_date, period.level))
        series_data.append((self.einddatum, einddatum_period.level))

        if not is_last_pgid_csv_row:
            only_one_row_exists = is_first_pgid_csv_row and is_last_pgid_csv_row
            if not only_one_row_exists:
                # remove last series to avoid duplicate dates in series. The first series of the 2nd row dominates
                # the last series of the 1st row (otherwise duplicate dates)
                series_data = series_data[:-1]

        # series_data = self._ugly_fix_peaks(series_data)
        return series_data

    @staticmethod
    def _ugly_fix_peaks(series_data: list) -> list:
        """I see some spykes/peak in timeseries + I don't have time find the cause of this. Better would be to do this
        whole project over (see Development in README.md)."""
        new_series_data = []

        for index, series in enumerate(series_data):
            if index == 0:
                new_series_data.append(series)
                continue
            try:
                _previous = series_data[index - 1]
                _next = series_data[index + 1]
            except IndexError:
                new_series_data.append(series)
                continue

            previous_date, previous_value = _previous
            current_date, current_value = series
            next_date, next_value = _next

            min_timedelta = min(current_date - previous_date, next_date - current_date)
            is_date_peak = min_timedelta < timedelta(days=2)
            if not is_date_peak:
                new_series_data.append(series)
                continue

            is_value_peak = previous_value == next_value != current_value
            if not is_value_peak:
                new_series_data.append(series)
                continue
            # TODO

        return new_series_data

    def get_period_in_between_date(self, month: int, day: int) -> ConstantPeriod:
        """
        Find the related period where period_start < (month, day) < period_end. The difficulty is that we compare
        month and days (no years),

        Example:
            self.periods:
                1) (4, 1, 1.375),  # First period starts April 1 and has level 1.375 mNAP
                2) (5, 1, 1.5),    # Second period starts May 1 and has level 1.5 mNAP
                3) (9, 1, 1.375),  # etc...
                4) (10, 1, 1.25)   # etc...

            Example 1:
                input = month=1, day=1
                returns period 4 (1.24) as Oct 1 < Jan 1 < Apr 1

            Example 2:
                input = month=4, day=14
                returns period 1 (1.375) as Apr 1 < Apr 14 < May 1

            Example 3:
                input = month=10, day=23
                returns period 4 (1.24) as Oct 1 < Oct 23 < Apr 1
        """
        dummy_year = 2000
        dummy_in_between_date = datetime(year=dummy_year, month=month, day=day)
        for period in self.periods:
            start_datetime_obj = datetime(year=dummy_year, month=period.start_month_int, day=period.start_day_int)
            end_datetime_obj = datetime(year=dummy_year, month=period.end_month_int, day=period.end_day_int)
            if start_datetime_obj <= dummy_in_between_date <= end_datetime_obj:
                return period
        # dummy_in_between_date must be between last and first period (= last and first element from self.periods)
        start_first_period_this_year = datetime(
            year=dummy_year, month=self.periods[0].start_month_int, day=self.periods[0].start_day_int
        )
        if dummy_in_between_date <= start_first_period_this_year:
            return self.periods[-1]

        start_last_period_this_year = datetime(
            year=dummy_year, month=self.periods[-1].start_month_int, day=self.periods[-1].start_day_int
        )
        start_first_period_next_year = datetime(
            year=dummy_year + 1, month=self.periods[0].start_month_int, day=self.periods[-1].start_day_int
        )
        if start_last_period_this_year < dummy_in_between_date < start_first_period_next_year:
            return self.periods[-1]

        raise AssertionError(f"code error, pgid={self.pgid}, periods={[x for x in self.periods]}")


class PeilbesluitPeil(BuilderBase):
    def __init__(self, eind_winter: str, begin_zomer: str, eind_zomer: str, begin_winter: str, **kwargs):
        assert [x for x in (eind_winter, begin_zomer, eind_zomer, begin_winter)]
        self.eind_winter = eind_winter
        self.begin_zomer = begin_zomer
        self.eind_zomer = eind_zomer
        self.begin_winter = begin_winter
        super().__init__(**kwargs)

    @property
    def periods(self) -> list:
        water_level_in_overgangs_period = (self.zomerpeil + self.winterpeil) / 2
        p1 = ConstantPeriod(start=self.eind_winter, end=self.begin_zomer, level=water_level_in_overgangs_period)
        p2 = ConstantPeriod(start=self.begin_zomer, end=self.eind_zomer, level=self.zomerpeil)
        p3 = ConstantPeriod(start=self.eind_zomer, end=self.begin_winter, level=water_level_in_overgangs_period)
        p4 = ConstantPeriod(start=self.begin_winter, end=self.eind_winter, level=self.winterpeil)
        return [p1, p2, p3, p4]


class Ondergrens(BuilderBase):
    def __init__(self, begin_zomer: str, eind_zomer: str, marge: float, **kwargs):
        assert [x for x in (begin_zomer, eind_zomer, marge)]
        self.begin_zomer = begin_zomer
        self.eind_zomer = eind_zomer
        self.marge = marge / 100  # convert from cm to m
        super().__init__(**kwargs)

    @property
    def periods(self) -> list:
        # In de overgangsperiod (tussen zomer- en winter, en vica-versa), dan moeten de marges wat groter zijn:
        #  - peilbesluitpeil heeft 3 verschillende niveaus/jaar: 1x winterpeil, 1x zomerpeil, 2x hetzelfde overganspeil
        #  - marges heeft 2 verschillende niveaus per jaar: wintermarge en zomermarge

        # ondermarges zitten aan zomer periode vast (begin tm eind zomer)
        p1 = ConstantPeriod(start=self.begin_zomer, end=self.eind_zomer, level=self.zomerpeil - self.marge)
        p2 = ConstantPeriod(start=self.eind_zomer, end=self.begin_zomer, level=self.winterpeil - self.marge)
        return [p1, p2]


class Bovengrens(BuilderBase):
    def __init__(self, begin_winter: str, eind_winter: str, marge: float, **kwargs):
        assert [x for x in (begin_winter, eind_winter, marge)]
        self.begin_winter = begin_winter
        self.eind_winter = eind_winter
        self.marge = marge / 100  # convert from cm to m
        super().__init__(**kwargs)

    @property
    def periods(self) -> list:
        # In de overgangsperiod (tussen zomer- en winter, en vica-versa), dan moeten de marges wat groter zijn:
        #  - peilbesluitpeil heeft 3 verschillende niveaus/jaar: 1x winterpeil, 1x zomerpeil, 2x hetzelfde overganspeil
        #  - marges heeft 2 verschillende niveaus per jaar: winter marge en zomer marge

        # bovenmarges zitten aan winter periode vast (begin winter tm eind winter)
        p1 = ConstantPeriod(start=self.eind_winter, end=self.begin_winter, level=self.zomerpeil + self.marge)
        p2 = ConstantPeriod(start=self.begin_winter, end=self.eind_winter, level=self.winterpeil + self.marge)
        return [p1, p2]
