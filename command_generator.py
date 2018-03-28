
import os
import yaml
from pylauncher.pylauncher import CommandlineGenerator, Commandline

NCINET_PATH = "/work/05187/ams13/maverick/ncinet_dev/run.py"
CONFIG_DIR = "/work/05187/ams13/maverick/Working/opt_config"


def make_commandline(params, index, in_name='hyper_config', out_name='results'):
    """Write config to file and return a commandline to run it"""
    in_name = os.path.join(CONFIG_DIR, in_name + str(index) + '.yml')
    out_name = os.path.join(CONFIG_DIR, out_name + str(index) + '.yml')

    # Write config
    with open(in_name, 'w') as conf_file:
        yaml.safe_dump(params, conf_file)

    # Generate commandline
    cmd_line_fstr = "python3 {app} --conf {config} --out_file {output}"
    return cmd_line_fstr.format(app=NCINET_PATH, config=in_name, output=out_name)


class HyperCommandGenerator(CommandlineGenerator):
    def __init__(self, parameter_settings):
        commands = []
        for i, params in enumerate(parameter_settings):
            cmd = make_commandline(params, i)
            commands.append(Commandline(cmd))
        CommandlineGenerator.__init__(self, list=commands)
