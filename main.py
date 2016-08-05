from datetime import datetime, timedelta
import configparser

import calpy.Logger as Logger
from calpy.caldav.Client import Client

Logger.setup_logging()

config = configparser.ConfigParser()
config.read(".config")
servers = []

for section in config.sections():
    if config.get(section, 'type') == 'server':
        try:
            row = {}
            for k in config.options(section):
                row[k] = config.get(section, k)
            servers.append(row)
        except configparser.NoOptionError:
            pass


client = Client(servers[0]['host'], servers[0]['port'], auth=(servers[0]['username'], servers[0]['password']),
                protocol=servers[0]['protocol'])

cals = client.discover()
print('found %s calendars' % len(cals))
for i in cals:
    i.load()
    events = i.get_events(datetime.today() - timedelta(days=7), end=datetime.today())
    for e in events:
        e.pretty_print()

