import logging
import re
from datetime import datetime, timedelta
from typing import List

from .VOBJECT import VOBJECT, MalformedVObjectException


class VTIMEZONE (VOBJECT):
    """ wrapper class for rfc2445 VTIMEZONE data

    provides parsing, pythonic data accessors and a few helper functions regarding VTIMEZONE data
    """

    _times = []  # type: List[dict]
    _weekdays = ['MO', 'TU', 'WE', 'TH', 'FR', 'SA', 'SU']

    def __init__(self, data: str):
        """ create a VTIMEZONE object from a caldav data block

        :param data: the full VTIMEZONE block in string format as returned from the CalDAV-server
        """

        # parsing notes:
        #    required fields: tzid
        #    optional fields: last-mod, tzurl, x-prop
        #
        #    required blocks: standard or daylight (at least once)
        #    required fields in block standard/daylight: dtstart, tzoffsetto, tzoffsetfrom
        #    optional fields in block standard/daylight: comment, rrule, rdate, tzname, x-prop
        logging.debug('creating VTIMEZONE from %s bytes of data' % len(data))

        data = VOBJECT.clean_vobject_block(data)

        try:
            self.tzid = re.search(r'^TZID:(.*?)$', data, re.MULTILINE).group(1)
        except AttributeError:
            raise MalformedVObjectException("Required property TZID not found")

        for m in re.finditer(r'^BEGIN:(STANDARD|DAYLIGHT)\n(.*?)END:(STANDARD|DAYLIGHT)$', data,
                             re.MULTILINE+re.DOTALL):
            try:
                dtstart = re.search(r'^DTSTART:(.*?)$', m.group(2), re.MULTILINE).group(1)
                tzoffsetfrom = re.search(r'TZOFFSETFROM:(.*?)$', m.group(2), re.MULTILINE).group(1)
                tzoffsetto = re.search(r'TZOFFSETTO:(.*?)$', m.group(2), re.MULTILINE).group(1)
                rrule = re.search(r'RRULE:(.*?)$', m.group(2), re.MULTILINE)

                values = {
                    'TYPE': m.group(1),
                    'DTSTART': dtstart,
                    'TZOFFSETFROM': tzoffsetfrom,
                    'TZOFFSETTO': tzoffsetto,
                }

                if rrule is not None:
                    values['RRULE'] = rrule.group(1)

                self._times.append(values)

            except AttributeError:
                raise MalformedVObjectException('Required Properties not found for %s block' % m.group(1))

    def localize(self, dt):
        """ localizes and returns a utc-timestamp according to the currently active timezone in this VTIMEZONE block """

        #
        #   TODO:   implement various RRULE styles (at least common ones..)
        #           possibly move rrule parsing into own classes because it's used by VEVENT as well
        #   TODO:   move get x-th day of month, first sunday, etc in separate functions

        logging.debug('localizing %s for timezone %s', (dt, self.tzid))

        cur_timezone = None
        cur_timestamp = None

        for t in self._times:
            dtstart = t['DTSTART']

            if 'RRULE' in t.keys():
                target_date = None
                vals = {}
                for k in t['RRULE'].split(';'):
                    (key, value) = k.split('=')
                    vals[key] = value

                if 'FREQ' in vals.keys():
                    if vals['FREQ'] == 'YEARLY':
                        month = int(vals['BYMONTH'])
                        day = vals['BYDAY']

                        if not day.isnumeric():
                            wd = day[-2:]
                            if day[:1] == "-":
                                cnt = int(day[1:2])
                                year = datetime.today().year
                                month = (month + 1) % 12
                                if month == 1:
                                    year += 1

                                start_date = datetime(year, int(month), 1)

                                day_num = start_date.weekday()
                                day_num_target = VTIMEZONE._weekdays.index(wd)
                                days_ago = (7 + day_num - day_num_target) % 7
                                if days_ago == 0:
                                    days_ago = 7
                                target_date = start_date - timedelta(days=days_ago + ((cnt-1)*7))

                            else:
                                cnt = int(day[:1])

                                start_date = datetime(datetime.today().year, int(month), 1)

                                day_num = start_date.weekday()
                                day_num_target = VTIMEZONE._weekdays.index(wd)
                                days_ago = (7 + day_num_target - day_num) % 7
                                if days_ago == 0:
                                    days_ago = 7
                                target_date = start_date + timedelta(days=days_ago + ((cnt-1)*7))

                if target_date is not None:
                    if cur_timestamp is None:
                        cur_timestamp = target_date
                        cur_timezone = t
                    else:
                        if target_date.date() < dt.date():
                            if cur_timestamp.date() > dt.date() or target_date.date() > cur_timestamp.date():
                                cur_timestamp = target_date
                                cur_timezone = t
                else:
                    logging.error('RRULE not implemented yet, no localization possible (%s)' % t['RRULE'])

        logging.debug('decided on timezone offset: %s' % cur_timezone['TZOFFSETTO'])

        m = re.search(r'([+-])?(\d\d)(\d\d)', cur_timezone['TZOFFSETTO'])

        if m.group(1) == "-":
            dt -= timedelta(hours=int(m.group(2)), minutes=int(m.group(3)))
        else:
            dt += timedelta(hours=int(m.group(2)), minutes=int(m.group(3)))

        logging.debug('localized to %s' % dt)
        return dt

    def __str__(self):
        return '<VTIMEZONE(%s)>' % self.tzid