from subprocess import Popen, PIPE
import platform

def ping_many_macos(request, errors=False):
    """ Ping many ips """

    # every `interval` seconds, launch `count` pings, abort if returns take longer than `timeout` seconds
    interval = .25 # can be float
    timeout = 3 # must be int
    count = 3

    commands = [f"ping -i {interval} -t {timeout} -c {count} {ip}" for ip in request.values()]

    # Check if running, return if so

    request['procs'] = []
    request['returns'] = ['-- ms' for ip in commands]

    for cmd in commands:

        if errors:
            stderr = PIPE
        else:
            stderr = None

        request['procs'] += [Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)]

    return request

def ping_many_windows(request, errors=False):
    """ Ping many ips """

    # every `interval` seconds, launch `count` pings, abort if returns take longer than `timeout` seconds
    interval = .25 # can be float
    timeout = 3 # must be int
    count = 3

    commands = [f"ping /w {timeout*1000} /n {count} {ip}" for ip in request.values()]

    # Check if running, return if so

    request['procs'] = []
    request['returns'] = ['-- ms' for ip in commands]

    for cmd in commands:

        if errors:
            stderr = PIPE
        else:
            stderr = None

        request['procs'] += [Popen(cmd, stdin=PIPE, stdout=PIPE, stderr=PIPE, shell=True)]

    return request

def ping_many(*args, **kwargs):
    if platform.system().lower() == 'darwin':
        return ping_many_macos(*args, **kwargs)
    elif platform.system().lower() == 'windows':
        return ping_many_windows(*args, **kwargs)
    else:
        raise(NotImplementedError(f"Platform {platform.system().lower()} is not supported"))

def parse_ping_macos(ping):
    """ macOS ping parsing """

    value = "-- ms"

    if ping is None or '100.0% packet loss' in ping:
        return value

    blob = ping.strip().split('\n')[-1] # "line after ping statistics"

    if blob == '':
        return value

    # get avg from roundtrip min/avg/max/stddev line
    value = (blob.split('/')[-3]) + ' ms'

    return value

def parse_ping_windows(ping):
    """ Windows ping parsing """

    value = "-- ms"

    # print('... Got ping response:', ping)

    if ping is None or '100% loss' in ping:
        return value

    blob = ping.split('\n')[-2] # "line after ping statistics"

    if blob == '':
        return value

    # get avg last line
    value = (blob.split(' = ')[-1]).strip() # includes ms

    return value

def parse_ping(*args, **kwargs):
    # print("... parse_ping")
    try:

        if platform.system().lower() == 'darwin':
            return parse_ping_macos(*args, **kwargs)
        elif platform.system().lower() == 'windows':
            return parse_ping_windows(*args, **kwargs)
        else:
            raise(NotImplementedError(f"Platform {platform.system().lower()} is not supported"))

    except Exception as e:
        print(f'... parse ping raised exception: {e}')


def get_pings_core(request):
    """ Get the returns of pinging many ips """

    for i, p in enumerate(request['procs']):

        if p.poll() is not None:

            # Done running, get output
            try:
                out,err = p.communicate()
                request['returns'][i] = parse_ping(str(out,'utf-8'))
                p.kill()

            except ValueError:
                # p has already been killed
                pass

    return request

def get_pings(*args, **kwargs):
    if platform.system().lower() in ['darwin', 'windows']:
        return get_pings_core(*args, **kwargs)
    else:
        raise(NotImplementedError(f"Platform {platform.system().lower()} is not supported"))
