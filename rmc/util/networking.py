import platform
import subprocess

def ping(host, timeout=5.0):
    """
    Returns True if host (str) responds to a ping request.
    Remember that a host may not respond to a ping (ICMP) request even if the host name is valid.
    """

    # Option for the number of packets as a function of
    param = '-n' if platform.system().lower()=='windows' else '-c'

    # Building the command. Ex: "ping -c 1 google.com"
    command = ['ping', param, '1', host]

    try:
        val = subprocess.call(command, timeout=timeout)
        return val == 0
    except subprocess.TimeoutExpired:
        return False
