import ConfigParser
from common import constants

CONFIG = None

def init(config_file=None):
    global CONFIG
    if CONFIG:
        return CONFIG
    if not config_file:
        config_file = constants.REPORT_CONFIG_FILE
    CONFIG = ConfigParser.SafeConfigParser()
    CONFIG.read(config_file)
    return CONFIG


def get_rhic_serve_config_info():
    return {
        "host": CONFIG.get("rhic_serve", "host"),
        "port": CONFIG.get("rhic_serve", "port"),
        "user": CONFIG.get("rhic_serve", "username"),
        "passwd": CONFIG.get("rhic_serve", "password")
    }
