"""
Overrides commandline generator to generate hyperparameter config files and then generate
commandlines using that file.
"""

import os
import yaml

from pylauncher import CommandlineGenerator, Commandline
from util import ensure_dir, pushdir

NCINET_PATH = "/work/05187/ams13/maverick/ncinet_dev/run.py"


def make_commandline(params, index, in_name='hyper_config', out_name='results'):
    """Write config to file and return a commandline to run it"""
    in_name = os.path.abspath(in_name + str(index) + '.yml')
    out_name = os.path.abspath(out_name + str(index) + '.yml')

    # Ensure dirs exist
    in_dir = os.path.dirname(in_name)
    out_dir = os.path.dirname(out_name)
    ensure_dir(in_dir)
    ensure_dir(out_dir)

    # Write config
    with open(in_name, 'w') as conf_file:
        yaml.safe_dump(params, conf_file)

    # Generate commandline
    cmd_line_fstr = "python3 {app} --conf {config} --out_file {output}"
    return cmd_line_fstr.format(app=NCINET_PATH, config=in_name, output=out_name)


class HyperCommandGenerator(CommandlineGenerator):
    def __init__(self, parameter_settings, config_dir=None):
        commands = []
        config_dir = config_dir if config_dir is not None else os.getcwd()
        ensure_dir(config_dir)

        # Change dir for config file creation
        with pushdir(config_dir):
            for i, params in enumerate(parameter_settings):
                cmd = make_commandline(params, i)
                commands.append(Commandline(cmd))

        CommandlineGenerator.__init__(self, list=commands)
