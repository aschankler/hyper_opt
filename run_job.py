
import os
from pylauncher import JobId, FileCommandlineGenerator, TaskGenerator, FileCompletion
from pylauncher import HostPool, HostListByName
from pylauncher import LauncherJob

from executor import EnvSSHExecutor
from command_generator import HyperCommandGenerator
from gen_param_dict import make_configs

CONFIG_DIR = "/work/05187/ams13/maverick/Working/opt_config"
#job_file = os.path.join(os.getcwd(), 'pylauncher/examples/commandlines')

jobid = JobId()
debug = "job+host"
workdir = "pylauncher_tmp" + str(jobid)
cores = 1

# This generates a list of command lines to run
#cmd_gen = FileCommandlineGenerator(job_file, cores=cores, debug=debug)
param_configs = make_configs('config_random.yaml', 4)
cmd_gen = HyperCommandGenerator(param_configs, config_dir=CONFIG_DIR)

# Wraps command line generators with info about whether tasks have completed/how to run the task
task_gen = TaskGenerator(cmd_gen,
                         completion=lambda x: FileCompletion(taskid=x, stamproot="expire", stampdir=workdir),
                         debug=debug)

# Set up the env for the worker shells
env_str = "module purge; module load gcc/4.9.3; module load cuda/8.0; module load cudnn/5.1;" \
          " module load python3/3.5.2; module load tensorflow-gpu/1.0.0\n"
env_str = "cd {path}\n".format(path=os.environ['PWD']) + env_str

# Wraps a commandline, writes to file, creates new commandline to exec the file.
executor = EnvSSHExecutor(env_str=env_str, workdir=workdir, debug=debug)

host_pool = HostPool(hostlist=HostListByName(), commandexecutor=executor, debug=debug)


# Also has a "maxruntime" param, a "gather_output" param
job = LauncherJob(
    hostpool=host_pool,
    taskgenerator=task_gen,
    debug=debug,
    gather_output='ncinet_output')


def main():
    job.run()
    print job.final_report()


if __name__ == '__main__':
    main()
