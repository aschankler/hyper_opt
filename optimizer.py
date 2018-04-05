"""
A simple hill-climbing optimizer for hyperparameter search.
"""

from __future__ import division
import numpy as np
import time
from typing import List, Tuple, Set, Sequence, Mapping, Union, Callable, Generic, TypeVar

# Type of an optimized parameter
P_type = TypeVar("P_type", int, float)
# Type of a complete set of parameters
Config_T = Mapping[str, Union[float, int]]


class Parameter(Generic[P_type]):
    """Optimization functions for a single parameter"""
    def __init__(self, name, initial, step, acceleration=1.4):
        # type: (str, P_type, P_type, float) -> None
        self.name = name
        self.integral = (type(initial) == int)
        self.value = initial
        self.step = step
        self.accel = acceleration

        # Stored data from the previous step
        self.best_score = -np.inf
        self.last_step_was_best = False
        self.step_taken = 0

    def add_delta(self):
        # type: () -> Tuple[P_type, ...]
        """Return new values to try for this param"""
        if not self.last_step_was_best:
            return self.value - self.step, self.value + self.step
        else:
            # Avoid calculating the backwards step
            return self.value + self.step * self.step_taken,

    def update(self, scores, best_score, was_best=False):
        # type: (Sequence[float], float, bool) -> None
        """Update the stepper based on results"""
        if (self.last_step_was_best and len(scores) != 1) or \
                (not self.last_step_was_best and len(scores) != 2):
            raise ValueError

        if self.last_step_was_best and was_best:
            # Accelerate the step
            self.step *= self.accel
            if self.integral:
                self.step = min(1, int(round(self.step)))

        if np.min(scores) < self.best_score:
            # Shrink the step
            self.step /= self.accel
            if self.integral:
                self.step = min(1, int(round(self.step)))

        # Record data on this step
        self.best_score = best_score

        if was_best:
            if not self.last_step_was_best:
                self.step_taken = -1 if np.argmax(scores) == 0 else 1
            self.last_step_was_best = True
        else:
            self.last_step_was_best = False
            self.step_taken = 0

    def serialize(self):
        # type: () -> str
        """Serializes object to yaml"""
        import yaml
        return yaml.dump(self)

    @staticmethod
    def from_yaml(yaml_str):
        # type: (str) -> Parameter
        """Reconstruct an object from serial"""
        import yaml
        return yaml.load(yaml_str)


class HillClimbOptimizer:
    """Simple hill climb optimizer"""
    def __init__(self, param_settings, mapper):
        # type: (Mapping[str, Config_T], Callable[[Sequence[Config_T]], List[float]]) -> None
        self.parameters = None                  # type: Set[Parameter]
        self.best_config = None                 # type: Config_T
        self.best_value = None                  # type: float
        self.last_best_value = None             # type: float

        self.tick = 1
        self.start_time = 0
        self.stop_flag = False
        self.out_file = None

        self.parameters = {Parameter(k, v['init'], v['step']) for k, v in param_settings.iteritems()}
        self.best_config = {k: v['init'] for k, v in param_settings.iteritems()}
        self.mapper = mapper

    def opt_step(self):
        # type: () -> None
        """Does one optimization step"""
        from copy import deepcopy
        self.last_best_value = self.best_value

        # Build configs to test
        config_map = {}
        for par in self.parameters:
            par_configs = []
            for param_value in par.add_delta():
                cfg = deepcopy(self.best_config)
                cfg[par.name] = param_value
                par_configs.append(cfg)
            config_map[par.name] = par_configs

        # Build a list of tags and # of configs
        def dict_to_list(input_map):
            """Turns a dict into a flat list of values and a tag list
            which can be used to reconstruct the dict"""
            value_list = []
            tag_list = []
            for k, v in input_map.iteritems():
                value_list.extend(v)
                tag_list.append((k, len(v)))
            return value_list, tag_list

        def list_to_dict(flat_list, tag_list):
            """Reconstructs a dict that was flattened using `dict_to_list`"""
            flat_idx = 0
            out_dict = {}
            for k, n_ell in tag_list:
                ell_list = flat_list[flat_idx:flat_idx + n_ell]
                out_dict[k] = ell_list
                flat_idx += n_ell
            return out_dict

        config_list, config_tags = dict_to_list(config_map)

        # Evaluate the starting point if this is the first step
        if self.best_value is None:
            config_list.append(self.best_config)

        # Map
        result_list = self.mapper(config_list)

        # Write data
        self.save_results(config_list, result_list)
        result_list = map(lambda x: x[0], result_list)

        # Update params if this is the first run
        if self.best_value is None:
            self.best_value = result_list.pop()
            for par in self.parameters:
                par.best_score = self.best_value

        # Find best score, best config
        result_dict = list_to_dict(result_list, config_tags)

        best_tag = None
        for tag, res in result_dict.iteritems():
            # Check if we found the best so far
            if max(res) > self.best_value:
                best_tag = tag
                self.best_value = max(res)
                i = np.argmax(res)
                self.best_config = config_map[tag][int(i)]

        # Update parameters
        for par in self.parameters:
            par.update(result_dict[par.name], self.best_value, par.name == best_tag)

    def save_results(self, configs, results):
        # type: (Sequence[Config_T], Sequence[float]) -> None
        """Write map output to file"""
        import yaml
        records = map(lambda cfg, res: {'config': cfg, 'result': res}, configs, results)
        with open(self.out_file, 'a') as out_file:
            out_file.write('---\n')
            yaml.dump(records, out_file)

    def write_data(self):
        import yaml
        params = [par.serialize() for par in self.parameters]

        records = {'round': self.tick,
                   'run_time': time.time() - self.start_time,
                   'config': self.best_config,
                   'value': self.best_value,
                   'param_data': params}

        with open(self.out_file, 'a') as out_file:
            out_file.write('---\n')
            yaml.dump(records, out_file)

    def should_stop(self, max_steps=None, max_time=None):
        if max_steps is not None and self.tick > max_steps:
            return True
        if max_time is not None and time.time() - self.start_time > max_time:
            return True
        return self.stop_flag

    def run(self, out_file, max_steps):
        self.start_time = time.time()
        self.out_file = out_file
        while not self.should_stop(max_steps=max_steps):
            self.opt_step()
            self.write_data()
            self.tick += 1
