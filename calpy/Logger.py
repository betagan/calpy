import logging
import platform
import os


def setup_logging():
    log_file = 'debug.log'

    if 'Windows' in platform.system():
        log_path = os.path.join(os.getenv('APPDATA'), 'betaworx.de', 'mirrorpy')
    else:
        log_path = "~/.mirrorpy/"

    if not os.path.exists(log_path):
        os.makedirs(log_path)

    # TODO: remove filemode='w' to stop it creating fresh log every time (debugging..)
    logging.basicConfig(filename=os.path.join(log_path, log_file), level=logging.DEBUG, filemode='w',
                        format="%(asctime)s|%(levelname)s|%(filename)s:%(lineno)s|%(funcName)20s()|%(message)s")