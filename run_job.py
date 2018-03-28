
import os
from pylauncher import JobId, FileCommandlineGenerator, TaskGenerator, FileCompletion
from pylauncher import HostPool, HostListByName
from pylauncher import LauncherJob

from executor import EnvSSHExecutor
from command_generator import HyperCommandGenerator
from gen_param_dict import make_configs

OPT_DIR = "/work/05187/ams13/maverick/Working/param_opt"
#job_file = os.path.join(os.getcwd(), 'pylauncher/examples/commandlines')

jobid = JobId()
debug = "job+host"
launcher_dir = os.path.join(OPT_DIR, "pylauncher_tmp" + str(jobid))
config_dir = os.path.join(OPT_DIR, "config")
cores = 1

# This generates a list of command lines to run
#cmd_gen = FileCommandlineGenerator(job_file, cores=cores, debug=debug)

from command_generator import pushdir
with pushdir("../hyper_opt"):
    param_configs = make_configs('config_random.yaml', 4)
cmd_gen = HyperCommandGenerator(param_configs, config_dir=config_dir)

# Wraps command line generators with info about whether tasks have completed/how to run the task
task_gen = TaskGenerator(cmd_gen,
                         completion=lambda x: FileCompletion(taskid=x, stamproot="expire", stampdir=launcher_dir),
                         debug=debug)

# Set up the env for the worker shells
env_str = "module purge; module load gcc/4.9.3; module load cuda/8.0; module load cudnn/5.1;" \
          " module load python3/3.5.2; module load tensorflow-gpu/1.0.0\n"
env_str = "cd {path}\n".format(path=os.environ['PWD']) + env_str

# Wraps a commandline, writes to file, creates new commandline to exec the file.
executor = EnvSSHExecutor(env_str=env_str, workdir=launcher_dir, debug=debug)

host_pool = HostPool(hostlist=HostListByName(), commandexecutor=executor, debug=debug)


# Also has a "maxruntime" param, a "gather_output" param
job = LauncherJob(
    hostpool=host_pool,
    taskgenerator=task_gen,
    debug=debug)

job.run()
print job.final_report()
