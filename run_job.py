
import os
from pylauncher import JobId, FileCommandlineGenerator, TaskGenerator, FileCompletion
from pylauncher import HostPool, HostListByName, SSHExecutor
from pylauncher import LauncherJob

job_file = os.path.join(os.getcwd(), 'pylauncher/examples/commandlines')

jobid = JobId()
debug = "job+host"
workdir = "pylauncher_tmp" + str(jobid)
cores = 1

# This generates a list of command lines to run
cmd_gen = FileCommandlineGenerator(job_file, cores=cores, debug=debug)

# Wraps command line generators with info about whether tasks have completed/how to run the task
task_gen = TaskGenerator(cmd_gen,
                         completion=lambda x: FileCompletion(taskid=x, stamproot="expire", stampdir=workdir),
                         debug=debug)

# Wraps a commandline, writes to file, creates new commandline to exec the file.
# This is where envt is exported, may need to modify
executor = SSHExecutor(workdir=workdir, debug=debug)

host_pool = HostPool(hostlist=HostListByName(), commandexecutor=executor, debug=debug)


# Also has a "maxruntime" param, a "gather_output" param
job = LauncherJob(
    hostpool=host_pool,
    taskgenerator=task_gen,
    debug=debug)

job.run()
print job.final_report()
