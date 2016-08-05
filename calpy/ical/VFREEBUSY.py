import re
from .VOBJECT import VOBJECT, MalformedVObjectException


class VFREEBUSY (VOBJECT):
    properties = {'CONTACT': False, 'DTSTART': False, 'DTEND': False, 'DURATION': False, 'DTSTAMP': False,
                  'ORGANIZER': False, 'UID': False, 'URL': False, 'ATTENDEE': False, 'COMMENT': False, 'RSTATUS': False,
                  'FREEBUSY': False, 'X-PROP': False}

    def __init__(self, obj : str):
        pass