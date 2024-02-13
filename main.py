"""
Each Part has consecutive set of Processes to be executed
Each Process requires Resource

Simulation Components follow the naming convention below.

[6Factor Concept]   [Class Object]
Part                Job
Process             Operation
Resource            Machine, Worker, Factory, Line, Transporter, etc.
Source              Source
Sink                Sink
Monitor             Monitor

Based on 'JSSP_6Factors_nobuffer_231113.py' file
Revised in 2023. 11. 15.
"""
from environment.Source import Source
from environment.Sink import Sink
from environment.Part import Job, Operation
from environment.Process import *
from environment.Resource import Machine
from environment.Monitor import Monitor
from postprocessing.PostProcessing import *
from visualization.Gantt import *
from visualization.GUI import GUI

import simpy, os, random
import pandas as pd
import numpy as np
from collections import OrderedDict

import quay


if __name__ == "__main__":

    import quay

    env = simpy.Environment()
    monitor = Monitor(filepath)
    model = dict()

    NUM_MACHINE = len(quay.quay_list)
    for i, q in enumerate(quay.quay_list):
        model[q] = Machine(env, i, q)

    for j, p in enumerate(quay.work_list):
        model[p] = Process(env, p, model, monitor)

    NUM_JOB = len(quay.job_list)
    # for i, j in enumerate(quay.job_list[:9]):
    for i, j in enumerate(quay.job_list[:10]):
        model['Source' + str(i + 1)] = Source(env, 'J-' + str(i + 1), model, monitor,
                                              job_type=quay.job_list[i], IAT=IAT, num_parts=1)

    model['Sink'] = Sink(env, monitor)

    env.run(5000)
    monitor.save_event()

    # In case of the situation where termination of the simulation greatly affects the machine utilization time,
    # it is necessary to terminate all the process at (SIMUL_TIME -1) and add up the process time to all machines

    machine_log = read_machine_log(filepath)
    gantt = Gantt(machine_log, len(machine_log), printmode=True, writemode=True)
    gui = GUI(gantt)
    # print()




