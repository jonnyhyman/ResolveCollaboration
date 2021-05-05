from subprocess import Popen, PIPE
import platform

def ping_many_macos(request, errors=False):

    commands = [f"ping -i 1 -t 9 -c 5 {ip}" for ip in request.values()]

    # Check if running, return if so

    request['procs'] = []
    request['returns'] = ['-- ms' for ip in commands]

    for cmd in commands:

        if errors:
            stderr = PIPE
        else:
            stderr = None

        request['procs'] += [Popen(cmd, stdout=PIPE, stderr=stderr, shell=True)]

    return request

def parse_ping_macos(ping):
    """ macOS ping parsing """

    value = "-- ms"

    if ping is None or 'Request timeout' in ping:
        return value

    blob = ping.split('\n')[-2] # "line after ping statistics"

    if blob == '':
        return value

    # get avg from roundtrip min/avg/max/stddev line
    value = (blob.split('/')[-3]) + ' ms'

    return value

def get_pings_macos(request):

    for i, p in enumerate(request['procs']):

        if p.poll() is not None:

            # Done running, get output
            try:
                out,err = p.communicate()
                request['returns'][i] = parse_ping_macos(str(out,'utf-8'))
                p.kill()

            except ValueError:
                # p has already been killed
                pass

    return request


def ping_many(*args, **kwargs):
    if platform.system().lower() == 'darwin':
        return ping_many_macos(*args, **kwargs)
    else:
        raise(NotImplementedError("Only macOS pinging supported"))

def parse_ping(*args, **kwargs):
    if platform.system().lower() == 'darwin':
        return parse_ping_macos(*args, **kwargs)
    else:
        raise(NotImplementedError("Only macOS pinging supported"))

def get_pings(*args, **kwargs):
    if platform.system().lower() == 'darwin':
        return get_pings_macos(*args, **kwargs)
    else:
        raise(NotImplementedError("Only macOS pinging supported"))