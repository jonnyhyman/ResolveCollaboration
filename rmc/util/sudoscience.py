from subprocess import Popen, PIPE
import subprocess
import os

def command_wrap(command, prompt):

    command = ("osascript "
                "-e "
                "'"
                f'do shell script "{command}" '
                f'with prompt "{prompt}" '
                "with administrator privileges "
                "without altering line endings"
                "'")

    return command

    #
    # return (
    #     f"sudo 'osascript -e "
    #     """do shell script """
    #     f'"{command}" with prompt "{prompt}" '
    #     'with administrator privileges '
    #     'without altering line endings '
    #     # "'"
    # )

def elevated_check_output(command,
                        timeout=None,
                        prompt = "Resolve Mission Control wants to run sudo"):


    command = command_wrap(command, prompt)

    print("Command >>>", command)

    try:
        out = subprocess.check_output(
            command,

            shell=True,
            timeout=timeout,
            stderr=subprocess.STDOUT)


        print("... Output:")
        print( str(out, 'utf-8') )

        return out

    except Exception as e:

        print("... Errors:")
        print( e )

def elevated_Popen(command,
                        prompt = "Resolve Mission Control wants to run sudo"):

    command = command_wrap(command, prompt)

    proc = Popen(command, shell=True, stdout=PIPE, stderr=PIPE)
    out, err = proc.communicate()

    out = str(out,'utf-8')
    err = str(err,'utf-8')

    print("Command >>>", command)
    print("... Output:")
    print( out )
    print("... Errors:")
    print( err )

    return out

def elevated_system(command,
                        prompt = "Resolve Mission Control wants to run sudo"):

    print("Command >>>", command)
    command = command_wrap(command, prompt)

    return os.system(command)
