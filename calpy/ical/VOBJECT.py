from datetime import datetime
import re
import logging


class MalformedVObjectException(Exception):
    pass


class VOBJECT:
    @staticmethod
    def clean_vobject_block(value: str):
        """ remove CRs and capitalize keywords """

        # get rid of windows carriage returns (^M)
        value = re.sub(r'&#13;$', '', value, flags=re.MULTILINE)

        # captitalize keywords
        lines = []
        for i in value.splitlines():
            try:
                idx = i.index(':')
                if i[:idx].upper() in ['BEGIN', 'END']:
                    lines.append(i.upper())
                else:
                    lines.append(i[:idx].upper()+i[idx:])  # FIXME this is probably bad because multiline text fields
            except ValueError:
                pass    # lines without colon are ignored
        logging.debug('parsed %s lines' % len(lines))
        return '\n'.join(lines)

    @staticmethod
    def parse_datetime(value: str):
        """ parse rfc2445 date/time value and return datetime.datetime """
        logging.debug('input value: %s' % value)

        if 'T' in value:
            try:
                return datetime.strptime(value, "%Y%m%dT%H%M%S")
            except ValueError:
                return datetime.strptime(value, "%Y%m%dT%H%M%SZ")
        else:
            return datetime.strptime(value, "%Y%m%d")