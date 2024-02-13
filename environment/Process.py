import simpy
import sys
import os
import numpy as np
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))

from environment.Monitor import *
from config import *
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))

NUM_JOB = None
NUM_MACHINE = None
def set_NUM_JOB(value):
    global NUM_JOB
    NUM_JOB = value
def set_NUM_MACHINE(value):
    global NUM_MACHINE
    NUM_MACHINE = value

class Process(object):
    def __init__(self, _env, _name, _model, _monitor):
        # input data
        self.env = _env
        self.name = _name  # 해당 프로세스의 이름
        self.model = _model
        self.monitor = _monitor

        self.in_buffer = simpy.FilterStore(_env, capacity=float('inf'))
        self.work_queue = simpy.FilterStore(_env, capacity=float('inf'))
        self.out_buffer = simpy.FilterStore(_env, capacity=float('inf'))
        global NUM_JOB
        self.work_waiting = [self.env.event() for i in range(NUM_JOB)]

        # get run functions in class
        _env.process(self.run())
        _env.process(self.dispatching())
        _env.process(self.to_next_process())

    """
    Class Description
    Process.run() : 작업 하나를 골라서 env.process()에 work를 추가시킴
    Process.work() : routing(machine의 결정)과 timeout이 일어나는 부분
    Process.to_next_process() : 다음 process로 전달
    
    [Scheduling Strategy가 적용되는 부분]
    Process.dispatching() : in_buffer에서 다음으로 작업할 Job을 결정
    Process.routing() : 가장 적절한 machine을 결정
    """

    def run(self):
        while True:
            """
            self.work_queue 에서 0 번째 element를 pop 해서 work 함수를 호출
            """
            # print(self.name,'\t','Waiting for part to arrive in work_queue...')
            part = yield self.work_queue.get()
            # print(self.name,'\t',part.name,'\t','Grabbed the part from the working queue')
            self.env.process(self.work(part))
            # print(self.name,'\t',part.name,'\t','work(part) executed!')

    def work(self, part):
        # print('function called8')
        operation = part.op[part.step]
        yield operation.requirements  # Check if former operations are all finished


        # 2. check the machines(resources) that are suitable for the process.
        machine, pt = self.routing(operation)

        """ This is where the scheduler enables the work to be processed. """
        # yield self.work_waiting[part.id]

        yield machine.availability.put('using')
        machine.status = 'Working'
        machine.turn_idle = self.env.now + pt

        # 3. Proceed & Record through console
        self.monitor.record(self.env.now, self.name, machine=machine.name,
                            part_name=part.name, event="Started")
        monitor_console(self.env.now, part, OBJECT, "Started on")

        yield self.env.timeout(pt)
        self.monitor.record(self.env.now, self.name, machine=machine.name,
                            part_name=part.name, event="Finished")
        monitor_console(self.env.now, part, OBJECT, "Finished on")

        machine.util_time += pt

        # 4. Send(route) to the out_part queue for routing and update the machine availability
        yield self.out_buffer.put(part)
        yield machine.availability.get()
        machine.status = 'Idle'

    def dispatching(self):
        """ 다음으로 진행할 작업을 결정하는 부분을 분리함 """
        while True:
            # print(self.name,'\t','Waiting for next arrival')
            # print(self.name,'\t','A new part arrived')
            part_ready = yield self.in_buffer.get()
            # print(self.name,'\t','grabbed a part from in_buffer')
            yield self.work_queue.put(part_ready)
            # print(self.name,'\t','put a part to work_queue')


    def routing(self, operation):
        """
        Pick the most suitable machine
        """

        if isinstance(operation.machine_available, list):

            # compatible machine list
            machine_list = operation.machine_available

            # compatible machine의 상태를 파악해서 idle 한 곳의 queue에 넣는 부분
            # TODO : 모든 machine이 idle하지 않은 경우에 대응할 수 있어야 함 -> 완료

            # Check if there are better options
            # Remark : 그런데 학습 방법에 따라서 현재 대기시간이 많이 남은 machine이더라도 그게 suitable하다고 판단되면 선택할 수 있어야 하지 않나?

            remaining_time = []
            for m in machine_list:

                if m.status == 'Idle':
                    remaining_time.append(0)
                else:
                    remaining_time.append(m.turn_idle - self.env.now)

            # index of the machine with the least remaining time
            least_remaining = np.argmin(remaining_time)
            machine = machine_list[least_remaining]

            # print(operation.name, 'The remaining time of compatible machines are:')
            # print([(machine_list[i],remaining_time[i]) for i in range(len(machine_list))])
            # print(operation.name,'is assigned on',machine.name)

            # process time on the certain machine
            if isinstance(operation.process_time, list):
                process_time = operation.process_time[least_remaining]
            else:
                process_time = operation.process_time

        else:  # if the compatible machine is determined and not given as list
            # use operation.machine to specify the name of the machine (e.g. 'M1')
            """
            In the simple JSSP problem, it is assumed that the machine is sorely designated
            (not given as a set, or a list)
            """
            machine = operation.machine_available
            process_time = operation.process_time

        # record the dispatching result
        operation.machine_determined = machine
        operation.process_time_determined = process_time
        return machine, process_time

    def to_next_process(self):
        while True:
            part = yield self.out_buffer.get()
            print('Part Arrived:',part.name)
            if part.step != part.num_process - 1:  # for operation 0,1,2,3 -> part.step = 1,2,3,4
                part.step += 1
                part.op[part.step].requirements.succeed()
                next_process = part.op[part.step].process  # i.e. model['Process0']
                # The machine is not assigned yet (to be determined further)
                yield next_process.in_buffer.put(part)
                part.loc = next_process.name
            else:
                self.model['Sink'].put(part)


if __name__ == "__main__":
    from Source import *
    from test_quay.test_quay import *
    from Sink import *
    from Resource import Machine
    from postprocessing.PostProcessing import read_machine_log
    from visualization.GUI import *
    from visualization.Gantt import *

    env = simpy.Environment()
    monitor = Monitor(filepath)
    NUM_JOB = 3
    model = {}
    jobtype1 = JobType('J-1', ['P1', 'P2', 'P3'],
                      [['M1'], ['M1', 'M3'], ['M2', 'M3']],
                      [10, 15, 10])
    jobtype2 = JobType('J-2', ['P1', 'P2', 'P3'],
                      [['M2'], ['M1', 'M3'], ['M2', 'M3']],
                      [8, [3,2], [5,6]])
    jobtype3 = JobType('J-3', ['P1', 'P2', 'P3'],
                      [['M1','M2'], ['M1', 'M3'], ['M2', 'M3']],
                      [10, [3,2], 8])
    model['Source1'] = Source(env, 'J1', model, monitor, job_type=jobtype1, IAT=IAT, num_parts=float('inf'))
    model['Source2'] = Source(env, 'J2', model, monitor, job_type=jobtype2, IAT=IAT, num_parts=float('inf'))
    model['Source3'] = Source(env, 'J3', model, monitor, job_type=jobtype3, IAT=IAT, num_parts=float('inf'))

    for j, p in enumerate(['P1', 'P2', 'P3']):
        model[p] = Process(env, p, model, monitor)

    for i, q in enumerate(['M1', 'M2', 'M3']):
        model[q] = Machine(env, i, q)

    model['Sink'] = Sink(env, monitor)
    env.run(50)
    monitor.save_event()
    machine_log = read_machine_log(filepath)
    gantt = Gantt(machine_log, len(machine_log), printmode=True, writemode=True)
    gui = GUI(gantt)
