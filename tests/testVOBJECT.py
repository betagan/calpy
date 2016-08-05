import unittest
from datetime import datetime

from calpy.ical.VOBJECT import VOBJECT


class TestVOBJECT(unittest.TestCase):

    def test_parse_datetime(self):
        self.assertEqual(VOBJECT.parse_datetime("20160721"), datetime.fromtimestamp(1469052000))
        self.assertEqual(VOBJECT.parse_datetime("20160721T130418Z"), datetime.fromtimestamp(1469099058))
        self.assertEqual(VOBJECT.parse_datetime("20160721T130418"), datetime.fromtimestamp(1469099058))

    def test_clean_vobject_block(self):
        val = "BEGIN:Vevent&#13;\ndtstart:20160730&#13;\nSUMMARY:Test Event\nEND:vEVENT&#13;\n"
        out = "BEGIN:VEVENT\nDTSTART:20160730\nSUMMARY:Test Event\nEND:VEVENT"
        self.assertEqual(VOBJECT.clean_vobject_block(val), out)