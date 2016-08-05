import unittest
from datetime import datetime

from calpy.ical.VEVENT import VEVENT


class TestVEVENT(unittest.TestCase):
    def setUp(self):
        self.ev = VEVENT('')

    def test_parse_duration(self):
        """ tests that get_duration parses an rfc2445 duration value type correctly and can fallback to
         datetime.timedelta if no duration value is present in the data """

        self.ev.duration = 'PT7H30M'
        self.assertEqual(self.ev.get_duration(), 27000)
        self.ev.duration = 'P7W'
        self.assertEqual(self.ev.get_duration(), 4233600)
        self.ev.duration = 'P3D12H'
        self.assertEqual(self.ev.get_duration(), 302400)
        self.ev.duration = 'PT4H15S'
        self.assertEqual(self.ev.get_duration(), 14415)

        self.ev.duration = None
        self.ev.dtstart = datetime(2016, 7, 30, 12, 30, 0)
        self.ev.dtend = datetime(2016, 7, 31, 13, 00, 30)
        self.assertEqual(self.ev.get_duration(), 88230)
