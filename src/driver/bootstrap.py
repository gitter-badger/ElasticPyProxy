from src.core.haproxyupdater.haproxyupdate import HaproxyUpdate
from src.core.nodefetchers.awsfetcher.awsfetcher import AwsFetcher
from src.core.nodefetchers.orchestrator import get_orchestrator_handler
from src.core.haproxyupdater.haproxyreloader import HaproxyReloader
import os

COULD_NOT_READ_PID_FILE = "COULD_NOT_READ_PID_FILE"

def bootstrap(**kwargs):
    config = kwargs.get("config")
    haproxy_config = config.get("haproxy")

    orchestrator = haproxy_config.get("orchestrator")

    orchestratorHandler = get_orchestrator_handler(config)
    asg_ips = orchestratorHandler.fetch()

    haproxyupdater = HaproxyUpdate(**haproxy_config)
    haproxyupdater.update_node_list(asg_ips)
    updated = haproxyupdater.update_haproxy_by_config_reload(update_only=True)

    if updated:
        running = start_if_not_running(config)
        return running, haproxyupdater, orchestratorHandler

    return updated, haproxyupdater, orchestratorHandler

def __is_haproxy_running(config):
    pid_file = config.get("pid_file")
    if not os.path.exists(pid_file):
        return False, None

    error = None

    try:
        with open(pid_file) as f:
            pid = int(f.readline())
    except Exception as ex:
        '''
            Log exception
        '''

        return False

    try:
        os.kill(pid, 0)
    except OSError:
        '''
            Haproxy is not running, log
        '''

        return False, None

    return True, None

def __start_if_not_running(config):
    
    is_haproxy_running, error = __is_haproxy_running(config)

    if is_haproxy_running:
        pass

    return True

