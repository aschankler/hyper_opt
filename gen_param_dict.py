
import numpy as np
import yaml
import sys

# This is needed for yaml to load the parameter objects
NCINET_PATH = "/work/05187/ams13/maverick/ncinet_dev"
sys.path.append(NCINET_PATH)


def make_configs(conf_file, n_configs):
    with open(conf_file, 'r') as conf_file:
        params = yaml.load(conf_file)
        param_list = []
        for _ in range(n_configs):
            param_dict = {k: v.render() for k, v in params['var_params'].iteritems()}

            # Purge numpy floats
            for k, v in param_dict.iteritems():
                if isinstance(v, np.float):
                    param_dict[k] = float(v)
                elif hasattr(v, '__iter__'):
                    param_dict[k] = map(float, v)

            param_dict.update(params['fixed_params'])
            param_list.append(param_dict)

    return param_list
