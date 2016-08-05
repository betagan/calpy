import logging
from typing import List

from calpy.caldav.Server import Server
from calpy.caldav.Calendar import Calendar


class Client(object):
    server = None     # type: Server

    def get_current_user_principal(self) -> str:
        headers = {'Depth': '0', 'Prefer': 'return-minimal'}
        req_data = """<d:propfind xmlns:d="DAV:"><d:prop><d:current-user-principal /></d:prop></d:propfind>"""
        xpath = ".//{DAV:}current-user-principal/{DAV:}href"

        return self.server.propfind_node_text('/', xpath, req_data, headers)

    def get_calendar_home_set(self, current_user_principal: str) -> str:
        headers = {'Depth': '0', 'Prefer': 'return-minimal'}
        req_data = """<d:propfind xmlns:d="DAV:" xmlns:c="urn:ietf:params:xml:ns:caldav"><d:prop>
                      <c:calendar-home-set /></d:prop></d:propfind>"""
        xpath = ".//{urn:ietf:params:xml:ns:caldav}calendar-home-set/{DAV:}href"

        return self.server.propfind_node_text(current_user_principal, xpath, req_data, headers)

    def get_calendars(self, calendar_home_set: str) -> List[Calendar]:
        """ fetch all Calendar collections for given calendar-home-set from the server

        performs a propfind with depth=1 for all resources under the given calendar-home-set and returns
        parsed instances of Tasks/Calendar for every VTODO/VEVENT calendar component found respectively

        :return: List of Calendar-collections
        """
        headers = {'Depth': '1', 'Prefer': 'return-minimal'}
        req_data = """<d:propfind xmlns:cs="http://calendarserver.org/ns/" xmlns:c="urn:ietf:params:xml:ns:caldav"
                      xmlns:d="DAV:" ><d:prop><d:resourcetype /><d:displayname /><cs:getctag />
                      <c:supported-calendar-component-set /></d:prop></d:propfind>"""
        xpath = ".//{DAV:}response"

        nodes = self.server.propfind_nodes(calendar_home_set, xpath, req_data, headers)

        calendars = []
        tasks = []

        for response in nodes:
            for supported in response.findall(".//{urn:ietf:params:xml:ns:caldav}supported-calendar-component-set/*"):
                component = supported.attrib.get('name', 'VUNKNOWN')

                if component == 'VTODO' or component == 'VEVENT':
                    cal = Calendar(component, self.server)
                    cal.ctag = response.find(".//{http://calendarserver.org/ns/}getctag").text
                    cal.path = response.find(".//{DAV:}href").text
                    cal.displayname = response.find(".//{DAV:}displayname").text

                    calendars.append(cal)

        return calendars

    def __init__(self, host:str, port=0, auth=None, protocol='https', verify_ssl=True):
        self.server = Server(host, port=port, auth=auth, protocol=protocol, verify_ssl=verify_ssl)

    def discover(self) -> List[Calendar]:
        current_user_principal = self.get_current_user_principal()

        if current_user_principal is None:
            return []

        calendar_home_set = self.get_calendar_home_set(current_user_principal)

        if calendar_home_set is None:
            return []

        return self.get_calendars(calendar_home_set)