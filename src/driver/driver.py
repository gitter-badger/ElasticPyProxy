from configparser import SafeConfigParser
import time
import optparse
import os
from .defaultparams import default_params
from .bootstrap import bootstrap
import logging

CONFIG_FILE = default_params.get("CONFIG_FILE")
LOCK_FILE = default_params.get("LOCK_FILE")

def drive():
    global CONFIG_FILE
    global LOCK_FILE

    # parse args
    parser = optparse.OptionParser()
    parser.add_option('-f', action="store", dest="config", help="Config file")
    options, args = parser.parse_args()

    if options.config:
        CONFIG_FILE = options.config

    config = __load_config()
    haproxy_config = config.get("haproxy")

    SLEEP_BEFORE_NEXT_RUN = int(haproxy_config.get("sleep_before_next_run", default_params.get("SLEEP_BEFORE_NEXT_RUN")))
    SLEEP_BEFORE_NEXT_LOCK_ATTEMPT = int(haproxy_config.get("sleep_before_next_lock_attempt", default_params.get("SLEEP_BEFORE_NEXT_LOCK_ATTEMPT")))
    LOG_DIR = haproxy_config.get("log_dir", default_params.get("LOG_DIR"))

    logger = __setup_logging(LOG_DIR)

    if not __sanitize_config(config):

        exit(2)

    running, haproxyupdater, orchestratorHandler = bootstrap(config=config)

    if not running:

        '''
            Error has already been logged. Exit with status code 2
        '''
        exit(2)

    '''
        After this point, Haproxy should be running with the lastest IPs
        fetched from the orchestrator.
    '''

    # Begin with state loop
    print ("Entering state loop...")
    i = 1
    while True:
        print ("run " + str(i))
        lock_aquired = __aquire_lock(haproxy_config.get("lock_dir"))
        if not lock_aquired:
            print ("asasasas")
            time.sleep(SLEEP_BEFORE_NEXT_LOCK_ATTEMPT)
            continue

        asg_ips = orchestratorHandler.fetch()
        print (asg_ips)
        haproxyupdater.update_node_list(asg_ips)
        updated = haproxyupdater.update_haproxy()
        print (updated)
        lock_released = __release_lock(haproxy_config.get("lock_dir"))
        time.sleep(SLEEP_BEFORE_NEXT_RUN)
        i += 1

def __setup_logging(log_dir):
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    logger_handler = logging.FileHandler(log_dir)
    logger_handler.setLevel(logging.DEBUG)
    logger_formatter = logging.Formatter(fmt='%(asctime)s %(levelname)-8s %(message)s',
                            datefmt='%Y-%m-%d %H:%M:%S')
    logger_handler.setFormatter(logger_formatter)
    logger.addHandler(logger_handler)

    return logger

def __load_config():
    parser = SafeConfigParser()
    parser.read(CONFIG_FILE)

    config = {}

    for section in parser.sections():
        config[section.lower()] = {}
        for name, value in parser.items(section):
            config[section.lower()][name] = value

    return config

def __can_aquire_lock(lock_dir):
    if not os.path.exists(lock_dir):
        return True

def __aquire_lock(lock_dir):
    lock_file = os.path.join(lock_dir, LOCK_FILE)
    try:
        if not os.path.exists(lock_file):
            with open(lock_file, "w") as lock_file:
                lock_file.write(str(os.getpid()))
            return True
        return False
    except Exception as ex:
        print (ex)
        return False

def __release_lock(lock_dir):
    lock_file = os.path.join(lock_dir, LOCK_FILE)
    try:
        if os.path.exists(lock_file):
            os.unlink(lock_file)
        return True
    except Exception as ex:
        print (ex)
        return False

def __sanitize_config(config):

    return True

if __name__ == "__main__":
    drive()
