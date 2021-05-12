
def postgres_restart_windows():
    import win32con
    import win32service
    import win32serviceutil

    accessSCM = win32con.GENERIC_READ
    accessSrv = win32service.SC_MANAGER_ALL_ACCESS

    #Open Service Control Manager
    hscm = win32service.OpenSCManager(None, None, accessSCM)

    #Enumerate Service Control Manager DB
    typeFilter = win32service.SERVICE_WIN32
    stateFilter = win32service.SERVICE_STATE_ALL

    statuses = win32service.EnumServicesStatus(hscm, typeFilter, stateFilter)

    for (short_name, desc, status) in statuses:
        if 'postgresql' in short_name.lower():
            win32serviceutil.RestartService(short_name, waitSeconds=5)
            return True
    return False

def postgres_restart_macos():
    from pathlib import Path
    import subprocess
    import psycopg2

    with psycopg2.connect(
                # the `postgres` db comes standard issue
                database="postgres",
                user="postgres",
                password="DaVinci",
                host="127.0.0.1",
                port="5432",
                connect_timeout=3,
              ) as connection:

        crs = connection.cursor()

        # Find where postgres is installed (datadir and pg_ctl in bin)
        crs.execute("select name, setting from pg_settings where name = 'data_directory';")
        data_dir = Path(crs.fetchall()[0][1])
        pg_ctl = data_dir.absolute().parent / 'bin/pg_ctl'

    # Change directory into PostgreSQL and then restart with pg_ctl
    command = ( f'''cd {data_dir.absolute().parent}; '''
                f'''sudo su postgres -c "{pg_ctl} restart -D {data_dir}"''')
    print("... restarting postgres >>>", command)

    try:
        out = subprocess.check_output(command,
                                    timeout=3,
                                    shell=True,
                                    stderr=subprocess.STDOUT)
    except subprocess.TimeoutExpired:
        # This is actually the expected route
        pass

    # Check if it worked
    try:
        with psycopg2.connect(
            # the `postgres` db comes standard issue
            database="postgres",
            user="postgres",
            password="DaVinci",
            host="127.0.0.1",
            port="5432",
            connect_timeout=3,
            ) as connection:

            return True
    except psycopg2.OperationalError:
        return False
