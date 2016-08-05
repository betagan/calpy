import logging
from datetime import datetime, timedelta
from typing import List

from calpy.caldav.Server import Server
from calpy.ical.VCALENDAR import VCALENDAR


class Calendar:
    """ wrapping class for a single Calendar on a CalDAV-Server

    an instance of this class is defined by the CalDAV-Server, the path to this calendar on the server and
    its etag.
    """

    server = None       # type: Server
    etag = None         # type: str
    path = None         # type: str
    ctag = None         # type: str
    displayname = None  # type: str
    entries = []        # type: List[VCALENDAR]
    type = []           # type: str

    def __init__(self, component: str, server: Server):
        self.server = server
        self.type = component

    def __str__(self):
        return "<Calendar(%s:%s)>" % (self.displayname, self.ctag)

    def get_events(self, start: datetime, end: datetime=None, duration: timedelta=None):
        if self.entries is None:
            return []

        results = []

        for e in self.entries:
            if start is None or e.is_on(start, end, duration):
                results.append(e)

        return results

    def load(self):
        """ load all available calendar data from the server (full load) """
        headers = {'Depth': 1, 'Prefer': 'return-minimal'}
        req_data = """<D:propfind xmlns:D="DAV:"><D:prop><D:getcontenttype/>
                <D:resourcetype/><D:getetag/></D:prop></D:propfind>"""
        xpath = ".//{DAV:}response"

        hrefs = []
        nodes = self.server.propfind_nodes(self.path, xpath, req_data, headers)

        for response in nodes:
            if response.find(".//{DAV:}resourcetype/{DAV:}collection") is None:
                try:
                    hrefs.append(response.find(".//{DAV:}href").text)
                except AttributeError:
                    logging.exception('malformed calendar event response')

        req_data = """<c:calendar-multiget xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav"><d:prop><d:getetag />
                 <c:calendar-data /></d:prop>\n"""

        for i in hrefs:
            req_data += "<d:href>%s</d:href>\n" % i

        req_data += "</c:calendar-multiget>"

        nodes = self.server.report_nodes(self.path, xpath, req_data, headers)

        self.entries = []

        for node in nodes:
            try:
                href = node.find(".//{DAV:}href").text
                etag = node.find(".//{DAV:}getetag").text
                data = node.find(".//{urn:ietf:params:xml:ns:caldav}calendar-data").text

                self.entries.append(VCALENDAR(href, etag, data))

            except AttributeError:
                logging.exception('malformed response tag or missing sub-tag')