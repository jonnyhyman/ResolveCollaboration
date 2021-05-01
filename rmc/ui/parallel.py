from subprocess import Popen, PIPE
from multiprocessing import Process

# ASYNCHRONOUS AND PARALLEL
class ParallelCommand:
    """ Runs a bunch of command line programs in parallel and captures returns """

    def __init__(self, commands, errors=False):

        self.procs = []
        self.returns = []

        for cmd in commands:
            if errors:
                stderr = PIPE
            else:
                stderr = None

            self.procs += [Popen(cmd, stdout=PIPE, stderr=stderr)]

        self.returns = [None for p in self.procs]

    def check_returns(self):

        # Check if running, return if so.
        for i, p in enumerate(self.procs):

            if p.poll() is not None:
                # Done running, get output
                try:
                    out,err = p.communicate()
                    self.returns[i] = str(out,'utf-8')
                    p.kill()

                except ValueError:
                    # p has already been killed
                    pass

        # make dealing with 1 command a bit better
        if len(self.returns) == 1:
            return self.returns[0]
        else:
            return self.returns
