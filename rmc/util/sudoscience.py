from subprocess import Popen, PIPE
import subprocess
import os

def command_wrap(command, prompt):

    # quotes are escaped because we're planning
    #  to run this in an osascript call (`elevated_check_output`)
    command = command.replace("'", "'\\''") # ' --> '\\''
    command = command.replace('"', '\\"') # " --> \\"


    command = ("osascript "
                "-e "
                "'"
                f'do shell script "{command}" '
                f'with prompt "{prompt}" '
                "with administrator privileges "
                "without altering line endings"
                "'")

    import pyperclip
    pyperclip.copy(command)

    # flat, a little easier to debug:
    # f"""osascript -e 'do shell script "{command}" with prompt "{prompt}" with administrator privileges without altering line endings'""")

    return command

def elevated_check_output(command,
                        timeout=None,
                        raise_errors=False,
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

    except subprocess.CalledProcessError:
        raise(PermissionError("User rejected sudo command authorization"))

    except Exception as e:

        if not raise_errors:
            print("... Errors:")
            print( e )
        else:
            raise(e)

def elevated_Popen(command,
                        errors = False,
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

    if 'User canceled' in err:
        raise(PermissionError("User rejected sudo command authorization"))

    if not errors:
        return out
    else:
        return out, err

def elevated_system(command,
                        prompt = "Resolve Mission Control wants to run sudo"):

    print("Command >>>", command)
    command = command_wrap(command, prompt)

    return os.system(command)
