import datetime
from logging import handlers
import os
import pathlib
import zoneinfo


class DatedFileHandler(handlers.BaseRotatingHandler):
    """
    Handler for logging to a set of files, which switches from one file
    to the next when the current date/time changes sufficiently.
    """
    rollover_threshold = "day"
    current_rollover_time = None
    next_rollover_time = None
    available_rollover_thresholds = [
        "year", "month", "week-of-year", "day-of-year", "day-of-week", "day", "hour", "minute"]
    timezone = zoneinfo.ZoneInfo("UTC")
    baseFilename_without_timestamp = None
    date_folder = None

    def __init__(
            self, filename, mode='a', rollover_threshold="day", encoding=None, delay=True, tz=zoneinfo.ZoneInfo("UTC"),
            date_folder=None
    ):
        """
        :param filename:
        :param mode:
        :param backupCount:
        :param rollover_threshold:
            Available values: week-of-year, day-of-year, day-of-week, day, hour, minute
            week-of-year = isocalendar()[1], Mon=1 - Sun=7
            day-of-year =
            day-of-week = isoweekday()

        :param encoding:
        :param delay: Default to True so the file isn't created until the first emit.
        :param tz:
        :param date_folder: Put the log file in a date folder formatted as provided.  If None, no folder.  "%Y-%m-%d"
        """
        if "b" not in mode:
            encoding = encoding or "utf-8"
        super().__init__(filename, mode, encoding=encoding, delay=delay)
        self.timezone = tz
        if rollover_threshold in self.available_rollover_thresholds:
            self.rollover_threshold = rollover_threshold
        self.rollover_delta = self.calculate_rollover_delta()
        self.calculate_rollover_times()
        self.date_folder = date_folder
        self.baseFilename_without_timestamp = self.baseFilename
        self.baseFilename = self.get_baseFilename()

    def calculate_next_rollover_time(self):
        return self.current_rollover_time + self.rollover_delta

    def calculate_rollover_time(self):
        return self.calculate_rollover_origin(self.now())

    def calculate_rollover_times(self):
        self.current_rollover_time = self.calculate_rollover_time()
        self.next_rollover_time = self.calculate_next_rollover_time()

    def calculate_rollover_delta(self):
        rollover_delta = datetime.timedelta(days=1)
        if self.rollover_threshold == "week-of-year":
            rollover_delta = datetime.timedelta(days=7)
        if self.rollover_threshold in ["day", "day-of-week", "day-of-year"]:
            rollover_delta = datetime.timedelta(days=1)
        if self.rollover_threshold == "hour":
            rollover_delta = datetime.timedelta(hours=1)
        if self.rollover_threshold == "minute":
            rollover_delta = datetime.timedelta(minutes=1)
        return rollover_delta

    def calculate_rollover_origin(self, dt):
        """
        If threshold is week-of year, returns the Monday of that iso week.
        If threshold is year, returns the Jan 1 of that year.
        :return:
        """
        if not isinstance(dt, datetime.datetime):
            dt = datetime.datetime.combine(dt, datetime.datetime.min.time())
            dt = dt.astimezone(self.timezone)
        # minute is the lowest threshold
        o = dt.replace(second=0, microsecond=0)
        if self.rollover_threshold in ["hour", "day", "day-of-week", "day-of-year", "week-of-year", "month", "year"]:
            o = o.replace(minute=0)
        if self.rollover_threshold in ["day", "day-of-week", "day-of-year", "week-of-year", "month", "year"]:
            o = o.replace(hour=0, minute=0)
        if self.rollover_threshold in ["day-of-week"]:
            # iso week starts on Monday.
            # weekday starts at Monday=0
            # only using it to calculate the monday date.  Don't need to worry about it conflicting with isocalendar's
            # monday=1 in week-of-year.
            o = o - datetime.timedelta(days=o.weekday())
        if self.rollover_threshold in ["week-of-year"]:
            # isocalendar counts week 1 as the week containing jan 4.
            # https://webspace.science.uu.nl/~gent0113/calendar/isocalendar.htm
            # use o.isocalendar().week to get 1-53
            pass
        if self.rollover_threshold in ["month", "year"]:
            o = o.replace(day=1)
        if self.rollover_threshold in ["year"]:
            o = o.replace(month=1, day=1)
        return o

    def doRollover(self):
        """
        Do a rollover, as described in __init__().
        """
        # The bulk is copied from logging.handlers.RotatingFileHandler
        if self.stream:
            self.stream.close()
            self.stream = None

        # Recalculate rollover times
        self.calculate_rollover_times()

        # Set the new baseFilename to include the now-current rollover time.
        self.baseFilename = self.get_baseFilename()

        if not self.delay:
            self.stream = self._open()

    @staticmethod
    def find_dated_file_handler(logger):
        for h in logger.handlers:
            if isinstance(h, DatedFileHandler):
                return h
        return None

    def get_baseFilename(self, at_time=None):
        """
        Get the log filename based on the current_rollover_time.
        :return:
        """
        at_time = at_time or self.current_rollover_time
        p = pathlib.Path(self.baseFilename_without_timestamp)
        format_str = "%Y-%m-%d_%H-%M-%S"  # _%Z_%z  Leaving out the timezone offset.
        if self.rollover_threshold in ["year"]:
            format_str = "%Y"
        if self.rollover_threshold in ["month"]:
            format_str = "%Y-%m"
        if self.rollover_threshold in ["week-of-year"]:
            # using iso version of year as it matches what is returned by %V
            # %W would return 00-53 (sunday-based).  %V returns 01-53 (jan 4th-based).
            format_str = "%G-%V"
        if self.rollover_threshold in ["day-of-year"]:
            format_str = "%Y-%j"
        if self.rollover_threshold in ["day-of-week"]:
            # TODO: needs work.  %u shows 1-7 but I want the monday date of the week.
            format_str = "%Y-%m-%u"
        if self.rollover_threshold in ["day"]:
            format_str = "%Y-%m-%d"
        if self.rollover_threshold in ["hour"]:
            format_str = "%Y-%m-%d_%H"
        if self.rollover_threshold in ["minute"]:
            format_str = "%Y-%m-%d_%H-%M"
        if self.date_folder:
            just_the_folder = p.parent / at_time.strftime(self.date_folder)
            just_the_folder.mkdir(parents=True, exist_ok=True)
            return str(just_the_folder / f"{at_time.strftime(format_str)}_{p.name}")
        return str(p.with_name(f"{at_time.strftime(format_str)}_{p.name}"))

    def now(self):
        return datetime.datetime.now(self.timezone)

    def shouldRollover(self, record):
        """
        Determine if rollover should occur.

        Check the date/time to see if the threshold has been reached.
        """
        # See bpo-45401: Never rollover anything other than regular files
        if os.path.exists(self.baseFilename) and not os.path.isfile(self.baseFilename):
            return False
        if self.stream is None:                 # delay was set...
            self.stream = self._open()
        if self.now() > self.next_rollover_time:
            return True
        return False
