import unittest

from scrap_logger import handlers


class TestDatedFileHandler(unittest.TestCase):
    def test_minute_threshold(self):
        handler = handlers.DatedFileHandler("filename.txt", rollover_threshold="minute")
        dt = handler.now()
        ro = handler.calculate_rollover_origin(dt)
        self.assertEqual(ro.year, dt.year)
        self.assertEqual(ro.month, dt.month)
        self.assertEqual(ro.day, dt.day)
        self.assertEqual(ro.hour, dt.hour)
        self.assertEqual(ro.minute, dt.minute)
        self.assertEqual(ro.second, 0)
        self.assertEqual(ro.microsecond, 0)
