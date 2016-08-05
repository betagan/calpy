import re
from datetime import datetime, timedelta
from tzlocal import get_localzone
import logging

from .VOBJECT import VOBJECT, MalformedVObjectException
from calpy.ical.VTODO import VTODO
from .VEVENT import VEVENT
from .VTIMEZONE import VTIMEZONE
from .VFREEBUSY import VFREEBUSY


class VCALENDAR (VOBJECT):
    href = None     # type: str
    etag = None     # type: str
    event = None    # type: VEVENT
    todo = None     # type: VTODO
    timezone = None # type: VTIMEZONE

    def __init__(self, href, etag, data: str):
        """
        create a VCALENDAR object from a caldav data block

        :param data: the full VCALENDAR block as returned from the CalDAV-server (as string)

        parser notes:
            required fields: VERSION, PRODID
            optional fields: CALSCALE, METHOD
            optional blocks: VEVENT, VTIMEZONE, VFREEBUSY
        """

        self.href = href
        self.etag = etag

        logging.debug('creating VCALENDAR with href="%s", etag="%s" and %s bytes of data' % (href, etag, len(data)))

        data = VOBJECT.clean_vobject_block(data)

        try:
            self.version = re.search(r'^VERSION:(.*?)$', data, re.MULTILINE).group(1)
        except AttributeError:
            raise MalformedVObjectException("Required property VERSION not found")

        try:
            self.prodid = re.search(r'^PRODID:(.*?)$', data, re.MULTILINE).group(1)
        except AttributeError:
            raise MalformedVObjectException("Required property PRODID not found")

        try:
            self.calscale = re.search(r'^CALSCALE:(.*?)$', data, re.MULTILINE).group(1)
        except AttributeError:
            self.calscale = None

        try:
            self.method = re.search(r'^METHOD:(.*?)$', data, re.MULTILINE).group(1)
        except AttributeError:
            self.method = None

        try:
            m = re.search(r'^BEGIN:VEVENT\n(.*?)END:VEVENT$', data, re.MULTILINE+re.DOTALL)
            if m is not None:
                self.event = VEVENT(m.group(1))
                logging.debug('Event added')
        except MalformedVObjectException:
            pass

        try:
            m = re.search(r'BEGIN:VTIMEZONE\n(.*?)END:VTIMEZONE$', data, re.MULTILINE+re.DOTALL)
            if m is not None:
                self.timezone = VTIMEZONE(m.group(1))
                logging.debug('Timezone added')
        except MalformedVObjectException:
            pass

        try:
            m = re.search(r'BEGIN:VFREEBUSY\n(.*?)END:VFREEBUSY$', data, re.MULTILINE+re.DOTALL)
            if m is not None:
                self.freebusy = VFREEBUSY(m.group(1))
                logging.debug('FreeBusy added')
        except MalformedVObjectException:
            pass

        try:
            m = re.search(r'BEGIN:VTODO\n(.*?)END:VTODO$', data, re.MULTILINE+re.DOTALL)
            if m is not None:
                self.todo = VTODO(m.group(1))
                logging.debug('Todo added')
        except MalformedVObjectException:
            pass

    def __str__(self):
        return '<VCALENDAR(%s;%s)>' % (self.etag, self.href)

    def is_on(self, start: datetime, end: datetime=None, duration: timedelta=None):
        logging.debug('testing etag %s for %s/%s/%s' % (self.etag, start, end, duration))
        if end is None:
            if duration is None:
                end = start
            else:
                end = start + duration

        #
        # aStart      aEnd
        # |____________|      bEnd
        #      |______________|
        #   bStart       |___________|
        #               aStart      aEnd
        #
        #  a timeperiod 'a' overlaps a time period 'b' if (aStart <= bEnd) and (aEnd >= bStart) as seen above.
        #
        res_event = (self.event is not None) and (self.event.start().date() <= end.date()) and \
                    (self.event.end().date() >= start.date())
        res_todo = (self.todo is not None) and (self.todo.start().date() <= end.date()) and \
                    (self.todo.end().date() >= start.date())

        return res_event or res_todo

    def next_date(self):
        # TODO: make this do something useful

        if self.event is None:
            return None

        if not self.event.recurring():
            dt = None
            if self.timezone is None:
                dt = get_localzone().fromutc(self.event.dtstart)
            else:
                dt = self.timezone.localize(self.event.dtstart)

            if dt.date() >= datetime.today().date():
                return dt
            else:
                return None

    def pretty_print(self):
        if self.event is not None:
            self.event.pretty_print()
        if self.todo is not None:
            self.todo.pretty_print()