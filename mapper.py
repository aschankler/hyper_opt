"""
Maps batches of ncinet evaluations across several nodes.
"""

import os
import time
from command_generator import make_commandline
from util import ensure_dir, pushdir
from pylauncher import Commandline, DynamicCommandlineGenerator
from pylauncher import LauncherJob, TaskGenerator, LauncherException, DebugTraceMsg


class DynamicNciCommandGen(DynamicCommandlineGenerator):
    """Takes a param dict, writes it to file and produces a training command"""
    def __init__(self, work_dir=None, **kwargs):
        DynamicCommandlineGenerator.__init__(self, **kwargs)
        self.work_dir = work_dir if work_dir is not None else os.getcwd()
        ensure_dir(self.work_dir)

    def append(self, param_dict):
        """Append a unix command to the internal structure of the generator"""
        command_no = self.ncommands
        self.ncommands += 1

        # Generate commandline
        with pushdir(self.work_dir):
            commandline = make_commandline(param_dict, command_no, out_name='results')

        self.list.append(Commandline(commandline))
        return command_no

    def get_results(self, command_no):
        """Return the output file of a given command"""
        import yaml
        output_filename = os.path.join(self.work_dir, 'results'+str(command_no)+'.yml')
        with open(output_filename, 'r') as out_file:
            result = yaml.load(out_file)
        return result


class LauncherMapper(LauncherJob):
    """Runs a launcher job to evaluate jobs in a list"""
    def __init__(self, cmd_gen, completion=None, task_dbg='', **kwargs):
        if kwargs.pop("taskgenerator", None) is not None:
            raise LauncherException("LauncherMapper constructs its own task generator")

        self.cmd_gen = cmd_gen
        self.starttime = time.time()
        self.runningtime = 0

        # Build the task generator
        task_gen = TaskGenerator(cmd_gen, completion=completion, debug=task_dbg)
        LauncherJob.__init__(self, taskgenerator=task_gen, **kwargs)

    def map(self, jobs, input_fn=None, output_fn=None):
        """Applies optional transform functions then passes args to commandline gen"""
        # Input transform
        if input_fn:
            jobs = map(input_fn, jobs)

        # Add jobs to queue
        job_ids = [self.cmd_gen.append(job) for job in jobs]

        # Run until jobs are done
        self.run()

        # Get results
        results = [self.cmd_gen.get_results(job_id) for job_id in job_ids]

        # Output transform
        if output_fn:
            results = map(output_fn, results)

        return results

    def tick(self):
        message = LauncherJob.tick(self)
        if message == "stalling":
            message = self.finish_or_continue()
        return message

    def run(self):
        """Invoke the launcher job, and call ``tick`` until all jobs are finished."""
        import re
        if re.search("host", self.debugs):
            self.hostpool.printhosts()

        while True:
            elapsed = time.time() - self.starttime
            runtime = "Time: %d" % int(elapsed)
            if self.maxruntime > 0:
                runtime += " (out of %d)" % int(self.maxruntime)
            DebugTraceMsg(runtime, self.debug, prefix="Job")

            if self.maxruntime > 0:
                if elapsed > self.maxruntime:
                    break

            res = self.tick()

            # update the restart file
            with open(self.workdir+"/queuestate", "w") as state_f:
                state_f.write(self.queue.savestate())

            # process the result
            if res == "finished":
                break

    def finish(self):
        self.hostpool.release()
        self.runningtime = time.time() - self.starttime
