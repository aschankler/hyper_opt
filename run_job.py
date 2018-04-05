
import os
import yaml
import numpy as np

from pylauncher import JobId, FileCompletion
from pylauncher import HostPool, HostListByName

from executor import EnvSSHExecutor
from optimizer import HillClimbOptimizer
from mapper import DynamicNciCommandGen, LauncherMapper
from util import pushdir, ensure_dir


# Dir to contain optimization files
opt_dir = "/work/05187/ams13/maverick/Working/param_opt"
ensure_dir(opt_dir)

# Make dirs for launcher records and ncinet config files
jobid = JobId()
debug = "job+host"
launcher_dir = os.path.join(opt_dir, "pylauncher_tmp" + str(jobid))
config_dir = os.path.join(opt_dir, "config" + str(jobid))

opt_out_file = os.path.join(opt_dir, 'optimizer_save')
opt_max_steps = 2

# Load config for optimization
opt_config_path = os.path.join(opt_dir, 'opt_config.yml')
with open(opt_config_path, 'r') as config_file:
    config_dict = yaml.load(config_file)

# Set up the env for the worker shells
env_str = "module purge; module load gcc/4.9.3; module load cuda/8.0; module load cudnn/5.1;" \
          " module load python3/3.5.2; module load tensorflow-gpu/1.0.0\n"
env_str = "cd {path}\n".format(path=os.environ['PWD']) + env_str

# Wraps a commandline, writes to file, creates new commandline to exec the file.
executor = EnvSSHExecutor(env_str=env_str, workdir=launcher_dir, debug=debug)
host_pool = HostPool(hostlist=HostListByName(), commandexecutor=executor, debug=debug)


# Define pre and post processing for the mapper
def input_fn(input_dict):
    """Add unoptimized parameters to the configuration"""
    input_dict.update(config_dict['fixed_params'])
    param_dict = {'initial_learning_rate': input_dict['initial_learning_rate'],
                  'n_filters': (input_dict['n_filt_0'], input_dict['n_filt_1'], input_dict['n_filt_2']),
                  'reg_weight': (input_dict['reg_0'], input_dict['reg_1'], input_dict['reg_2']),
                  'train_batch_size': input_dict['train_batch_size'],
                  'epochs_per_decay': input_dict['epochs_per_decay'],
                  'filter_size': input_dict['filter_size'], 'max_steps': input_dict['max_steps']}
    return param_dict


def output_fn(result_dict):
    """Picks out error, averages, inverts"""
    res = np.mean(result_dict['error'])
    return - float(res)


# construct mapper
cmd_gen = DynamicNciCommandGen(work_dir=config_dir)

with pushdir(opt_dir):
    mapper = LauncherMapper(
        cmd_gen,
        completion=lambda x: FileCompletion(taskid=x, stamproot='expire', stampdir=launcher_dir),
        task_dbg=debug,
        hostpool=host_pool,
        debug=debug,
        gather_output='ncinet_out',
        delay=30.)

    map_fn = lambda job_list: mapper.map(job_list, input_fn=input_fn, output_fn=output_fn)

    optimizer = HillClimbOptimizer(config_dict['opt_params'], map_fn)

    optimizer.run(opt_out_file, opt_max_steps)

    print mapper.final_report()
    mapper.finish()
