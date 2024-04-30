import os
import numpy as np
import simpy
from environment.Sink import *
from environment.Process import *
from environment.Part import *
from environment.Resource import *
from environment.Source import *
from environment.Monitor import *


class FJSP:
    def __init__(self, cfg, data):
        self.model = dict()
        self.sim_env = simpy.Environment()
        self.monitor = Monitor(cfg.filepath)
        self._modeling(self.sim_env, cfg, data)
        self.state_dim = 10
        self.action_dim = 10
        pass

    def step(self, action):
        pass

    def _modeling(self, env, cfg, data):
        for i, q in enumerate(data[0]):
            self.model[q] = Machine(env, i, q)
        for j, p in enumerate(data[1]):
            self.model[p] = Process(cfg, env, p, self.model, self.monitor)
        for i, j in enumerate(data[2]):
            self.model['Source' + str(i + 1)] = Source(cfg, env, 'J' + str(i + 1), self.model, self.monitor,
                                                  job_type=j, IAT=cfg.IAT, num_parts=1)

    def reset(self):
        pass

    def _get_state(self):
        state = 0.0
        return state

    def _calculate_reward(self):
        reward = 0.0
        return reward

    def get_logs(self, path=None):
        log = 0.0
        return log

