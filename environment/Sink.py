from environment.Monitor import *
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))

# from config import CONSOLE_MODE

# region Sink
class Sink(object):
    def __init__(self, cfg, env, monitor):
        self.env = env
        self.name = 'Sink'
        self.monitor = monitor
        self.cfg = cfg

        # Sink를 통해 끝마친 Part의 갯수
        self.parts_rec = 0
        # 마지막 Part가 도착한 시간
        self.last_arrival = 0.0
        # self.finished = simpy.Event()

    # put function
    def put(self, part):
        self.parts_rec += 1
        self.last_arrival = self.env.now
        if self.cfg.CONSOLE_MODE :

            monitor_console(self.env.now, part, command="Completed on")
        self.monitor.record(self.env.now, self.name, machine=None,
                            part_name=part.name, event="Completed")

        if self.parts_rec == self.cfg.num_job:
            self.last_arrival = self.env.now

# endregion
