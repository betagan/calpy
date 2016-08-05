import re
import logging
from datetime import timedelta, datetime

from .VOBJECT import VOBJECT


class VEVENT (VOBJECT):
    dtstart = None      # type: datetime
    dtend = None        # type: datetime
    duration = None     # type: int
    rawdata = None      # type: str

    def start(self):
        """ event start timestamp """

        if self.dtstart is None:
            logging.warning('DTSTART is None, dumping raw data: %s' % self.rawdata)
        return self.dtstart

    def end(self):
        """ event end timstamp """

        if self.dtend is not None:
            return self.dtend
        elif self.duration is not None:
            return self.dtstart + timedelta(seconds=self.get_duration())
        else:
            logging.warning('no DTEND or DURATION present, returning DTSTART instead. raw dump: %s ' % self.rawdata)
            return self.dtstart

    def get_duration(self):
        """
        returns event duration in seconds

        :return: event duration in seconds

         if the DURATION property is available on the original VEVENT object, that value is parsed and returned
         otherwise the timedelta between DTSTART and DTEND is computed and returned

         DURATION is expected to be of value type duration as specified in rfc2445
        """
        if self.duration is not None:
            val = 0
            m = re.search(r'P(?:(\d+)W)?(?:(\d+)D)?T?(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?', self.duration)
            if m.group(1) is not None:
                val += int(m.group(1)) * 7*24*60*60
            if m.group(2) is not None:
                val += int(m.group(2)) * 24*60*60
            if m.group(3) is not None:
                val += int(m.group(3)) * 60*60
            if m.group(4) is not None:
                val += int(m.group(4)) * 60
            if m.group(5) is not None:
                val += int(m.group(5))

            return val
        else:
            try:
                return int((self.dtend - self.dtstart).total_seconds())
            except TypeError:
                return 0

    def __init__(self, data: str):
        logging.debug('creating event from %s bytes of data' % len(data))

        self.rawdata = data
        data = VOBJECT.clean_vobject_block(data)

        try:
            self.description = re.search(r'^DESCRIPTION:(.*?)$', data, re.MULTILINE).group(1)
        except AttributeError:
            self.description = None

        try:
            self.summary = re.search(r'^SUMMARY:(.*?)$', data, re.MULTILINE).group(1)
        except AttributeError:
            self.summary = None

        try:
            self.dtstart = self.parse_datetime(re.search(r'^DTSTART.*:(.*?)$', data, re.MULTILINE).group(1))
        except AttributeError:
            self.dtstart = None

        try:
            self.dtend = self.parse_datetime(re.search(r'^DTEND.*:(.*?)$', data, re.MULTILINE).group(1))
        except AttributeError:
            self.dtend = None

        try:
            self.duration = re.search(r'^DURATION:(.*?)$', data, re.MULTILINE).group(1)
        except AttributeError:
            self.duration = None

        self.rrules = []
        for i in re.finditer(r'^RRULE:(.*?)$', data, re.MULTILINE):
            self.rrules.append(i.group(1))

        """
            ; the following are optional,
            ; but MUST NOT occur more than once

            class / created / description / dtstart / geo /
            last - mod / location / organizer / priority /
            dtstamp / seq / status / summary / transp /
            uid / url / recurid /

            ; either 'dtend' or 'duration' may appear in
            ; a 'eventprop', but 'dtend' and 'duration'
            ; MUST NOT occur in the same 'eventprop'

            dtend / duration /

            ; the following are optional,
            ; and MAY occur more than once

            attach / attendee / categories / comment /
            contact / exdate / exrule / rstatus / related /
            resources / rdate / rrule / x-prop
        """

    def recurring(self):
        return len(self.rrules) > 0

    def __str__(self):
        return '<VEVENT(%s;%s)>' % (self.dtstart, self.summary)

    def pretty_print(self):
        print("--------------------------------------------------")
        print("summary:     %s" % self.summary)
        print("start:       %s" % self.start())
        print("end:         %s" % self.end())
        print("--------------------------------------------------")