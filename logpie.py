# encoding=utf-8
"""
The main interface of LogPie
"""

import json
import logging
import subprocess
from reader.generate import make_reader

CONFIGURATION = 'logpie.json'
DEFAULT_CONFIG = {
    "gen-reader-with": "Python",
    "src-path": "./"
}


def read_config():
    logger = logging.getLogger("Configurator")
    try:
        fp = open(CONFIGURATION)
        configuration = json.load(fp)
        fp.close()
        if set(configuration.keys()) != set(DEFAULT_CONFIG.keys()):
            logger.error("Invalid configuration")
            logger.debug("DEBUG - NO FALL BACK")
            # return None
    except IOError as ioe:
        logger.error("Cannot access configuration: IOError: %s", CONFIGURATION)
    except ValueError as ve:
        logger.error("Cannot parse configuration: ValueError: %s",
                     CONFIGURATION)
    except Exception as e:
        logger.error("Undefined error: %s", e)
    else:
        return configuration


def main():
    logger = logging.getLogger("Main")
    configure = read_config()
    if configure is None:
        logger.warning("Config failed. Falling back to default.")
        configure = DEFAULT_CONFIG
    # build reader
    logger.info("BUILDING READER")
    logsys = configure['logsys']
    pattern = configure['pattern']
    path = make_reader(logsys, pattern)
    runnable = configure['python-runnable']
    # use reader
    s, ret = subprocess.getstatusoutput(' '.join([runnable, path]))
    print(s, ret)
    # further not implemented


if __name__ == '__main__':
    main()