import datetime
import pathlib
import unittest

from scrap_logger import handlers


class TestDatedFileHandler(unittest.TestCase):
    def test_minute_threshold_calculate_rollover_origin(self):
        handler = handlers.DatedFileHandler("filename.txt", rollover_threshold="minute")
        dt = handler.now()
        ro = handler.calculate_rollover_origin(dt)
        self.assertEqual(ro.date(), dt.date())
        self.assertEqual(ro.hour, dt.hour)
        self.assertEqual(ro.minute, dt.minute)
        self.assertEqual(ro.second, 0)
        self.assertEqual(ro.microsecond, 0)

    def test_hour_threshold_calculate_rollover_origin(self):
        handler = handlers.DatedFileHandler("filename.txt", rollover_threshold="hour")
        dt = handler.now()
        ro = handler.calculate_rollover_origin(dt)
        self.assertEqual(ro.date(), dt.date())
        self.assertEqual(ro.hour, dt.hour)
        self.assertEqual(ro.minute, 0)
        self.assertEqual(ro.second, 0)
        self.assertEqual(ro.microsecond, 0)

    def test_day_threshold_calculate_rollover_origin(self):
        handler = handlers.DatedFileHandler("filename.txt", rollover_threshold="day")
        dt = handler.now()
        ro = handler.calculate_rollover_origin(dt)
        self.assertEqual(ro.date(), dt.date())
        self.assertEqual(ro.time(), datetime.datetime.min.time())

    def test_dayofweek_threshold_calculate_rollover_origin(self):
        handler = handlers.DatedFileHandler("filename.txt", rollover_threshold="day-of-week")
        dates = [
            (datetime.datetime(2023, 9, 25, 7, 31, 0), 25),
            (datetime.datetime(2023, 9, 24, 7, 31, 0), 18),
            (datetime.datetime(2023, 9, 23, 7, 31, 0), 18),
            (datetime.datetime(2023, 9, 22, 7, 31, 0), 18),
            (datetime.datetime(2023, 9, 21, 7, 31, 0), 18),
            (datetime.datetime(2023, 9, 20, 7, 31, 0), 18),
            (datetime.datetime(2023, 9, 19, 7, 31, 0), 18),
            (datetime.datetime(2023, 9, 18, 7, 31, 0), 18),
            (datetime.datetime(2023, 9, 17, 7, 31, 0), 11),
        ]
        for dt, expected_dow in dates:
            with self.subTest(dt=dt, expected_dow=expected_dow):
                ro = handler.calculate_rollover_origin(dt)
                self.assertEqual(ro.year, dt.year)
                self.assertEqual(ro.month, dt.month)
                self.assertEqual(ro.day, expected_dow)
                self.assertEqual(ro.time(), datetime.datetime.min.time())

    def test_weekofyear_threshold_calculate_rollover_origin(self):
        # isocalendar counts week 1 as the week containing jan 4.
        # https://webspace.science.uu.nl/~gent0113/calendar/isocalendar.htm
        # use o.isocalendar().week to get 1-53
        handler = handlers.DatedFileHandler("filename.txt", rollover_threshold="week-of-year")
        dates = [
            # Odd case where last few days of a year are in the next year's week 1.
            (datetime.datetime(2003, 12, 29, 7, 31, 55), (2004, 1, 1)),
            # Odd case where first day of a year is in week 53 of previous year
            (datetime.datetime(2016, 1, 1, 7, 31, 55), (2015, 53, 5)),
            # Dec dates straddling the iso year/week
            (datetime.datetime(2014, 12, 28, 7, 31, 55), (2014, 52, 7)),
            (datetime.datetime(2014, 12, 29, 7, 31, 55), (2015, 1, 1)),
            # Jan dates straddling the iso year/week
            (datetime.datetime(2009, 12, 31, 7, 31, 55), (2009, 53, 4)),
            (datetime.datetime(2010, 1, 1, 7, 31, 55), (2009, 53, 5)),
            (datetime.datetime(2010, 1, 4, 7, 31, 55), (2010, 1, 1)),
        ]
        for dt, expected_dow in dates:
            with self.subTest(dt=dt, expected_dow=expected_dow):
                ro = handler.calculate_rollover_origin(dt)
                self.assertEqual(ro.year, dt.year)
                self.assertEqual(ro.month, dt.month)
                self.assertEqual(ro.isocalendar(), expected_dow)
                self.assertEqual(ro.time(), datetime.datetime.min.time())

    def test_month_threshold_calculate_rollover_origin(self):
        handler = handlers.DatedFileHandler("filename.txt", rollover_threshold="month")
        dt = handler.now()
        ro = handler.calculate_rollover_origin(dt)
        self.assertEqual(ro.year, dt.year)
        self.assertEqual(ro.month, dt.month)
        self.assertEqual(ro.day, 1)
        self.assertEqual(ro.time(), datetime.datetime.min.time())

    def test_year_threshold_calculate_rollover_origin(self):
        handler = handlers.DatedFileHandler("filename.txt", rollover_threshold="year")
        dt = handler.now()
        ro = handler.calculate_rollover_origin(dt)
        self.assertEqual(ro.year, dt.year)
        self.assertEqual(ro.month, 1)
        self.assertEqual(ro.day, 1)
        self.assertEqual(ro.time(), datetime.datetime.min.time())

    def test_get_baseFilename(self):
        handler = handlers.DatedFileHandler("filename.txt", rollover_threshold="minute")
        dt = datetime.datetime(2023, 9, 23, 7, 31, 0)
        thresholds = [
            ("year", "2023_filename.txt"),
            ("month", "2023-09_filename.txt"),
            ("week-of-year", "2023-38_filename.txt"),
            ("day-of-year", "2023-266_filename.txt"),
            ("day-of-week", "2023-09-18_filename.txt"),
            ("day", "2023-09-23_filename.txt"),
            ("hour", "2023-09-23_07_filename.txt"),
            ("minute", "2023-09-23_07-31_filename.txt"),
        ]
        for threshold, expected_filename in thresholds:
            with self.subTest(threshold=threshold, expected_filename=expected_filename):
                handler.rollover_threshold = threshold
                bfn = pathlib.Path(handler.get_baseFilename(at_time=dt))
                self.assertEqual(bfn.name, expected_filename)
