import requests
import logging
import xml.etree.ElementTree as Xml
from typing import List

from http.client import responses as http_codes
from numbers import Number


class OperationFailed(Exception):
    @staticmethod
    def _codestr(code):
        return http_codes.get(code, 'UNKNOWN')

    _OPERATIONS = dict(
        HEAD="get header",
        GET="get",
        PUT="put",
        DELETE="delete",
        PROPFIND="propfind",
        REPORT="report"
        )

    def __init__(self, method, path, expected_code, actual_code):
        self.method = method
        self.path = path
        self.expected_code = expected_code
        self.actual_code = actual_code
        operation_name = self._OPERATIONS[method]
        self.reason = 'Failed to {operation_name} "{path}"'.format(**locals())
        expected_codes = (expected_code,) if isinstance(expected_code, Number) else expected_code
        expected_codes_str = ", ".join('{0} {1}'.format(code, self._codestr(code)) for code in expected_codes)
        actual_code_str = self._codestr(actual_code)
        msg = '''\
{self.reason}.
  Operation     :  {method} {path}
  Expected code :  {expected_codes_str}
  Actual code   :  {actual_code} {actual_code_str}'''.format(**locals())
        super(OperationFailed, self).__init__(msg)


class Server(object):
    def __init__(self, host, port=0, auth=None,
                 protocol='https', verify_ssl=True, path=None):
        if not port:
            port = 443 if protocol == 'https' else 80

        self.baseurl = '{0}://{1}:{2}'.format(protocol, host, port)

        if path:
            self.baseurl = '{0}/{1}'.format(self.baseurl, path)

        self.session = requests.session()
        self.session.verify = verify_ssl
        self.session.stream = True

        if auth:
            self.session.auth = auth

    def send(self, method, path, expected_code, **kwargs) -> requests.Response:
        url = self._get_url(path)
        response = self.session.request(method, url, allow_redirects=False, **kwargs)
        if isinstance(expected_code, Number) and response.status_code != expected_code \
            or not isinstance(expected_code, Number) and response.status_code not in expected_code:
            raise OperationFailed(method, path, expected_code, response.status_code)
        return response

    def _get_url(self, path) -> str:
        path = str(path).strip()
        if path.startswith('/'):
            return self.baseurl + path
        return "".join((self.baseurl, '/', path))

    def request_xml(self, method: str, url: str, req_data:str, headers=None) -> Xml.ElementTree:
        try:
            response = self.send(method, url, 207, data=req_data, headers=headers)
        except OperationFailed:
            logging.exception('request failed')
            return None
        try:
            tree = Xml.fromstring(response.content)
        except (Xml.ParseError, TypeError):
            logging.exception('Response malformed')
            return None

        return tree

    def propfind(self, url: str, req_data: str, headers=None) -> Xml.ElementTree:
        return self.request_xml("PROPFIND", url, req_data, headers)

    def report(self, url: str, req_data: str, headers=None) -> Xml.ElementTree:
        return self.request_xml("REPORT", url, req_data, headers)

    def propfind_nodes(self, url: str, xpath: str, req_data:str, headers=None) -> List[Xml.ElementTree]:
        tree = self.propfind(url, req_data, headers)
        if tree is None:
            return []

        return tree.findall(xpath)

    def report_nodes(self, url: str, xpath: str, req_data:str, headers=None) -> List[Xml.ElementTree]:
        tree = self.report(url, req_data, headers)
        if tree is None:
            return []

        return tree.findall(xpath)

    def propfind_node_text(self, url: str, xpath: str, req_data: str, headers=None) -> str:
        node = self.propfind(url, req_data, headers)

        if node is None:
            return None

        res = node.find(xpath)
        if res is None:
            # TODO: add detection for errors like unauthorized?
            logging.error('server respondeded with status 207 but target node %s not found in response XML' % xpath)
            return None

        logging.debug('target node found with value: %s' % res.text)
        return res.text
