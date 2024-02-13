import simpy
import numpy as np
from environment.Part import Job, Operation
from environment.Monitor import Monitor
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
from config import *


# region Source
class Source(object):
    def __init__(self, _env, _name, _model, _monitor, job_type, IAT='exponential(1)', num_parts=float('inf')):
        self.env = _env
        self.name = _name  # 해당 Source의 이름
        self.model = _model
        self.monitor = _monitor
        self.job_type = job_type  # Source가 생산하는 Part의 Job Type, 클래스 인자를 받을 예정
        self.IAT = IAT  # Source가 생성하는 Part의 IAT(jobtype을 통한 Part 생성)
        self.num_parts = num_parts  # Source가 생성하는 Part의 갯수

        self.rec = 0  # 생성된 Part의 갯수를 기록하는 변수
        self.generated_parts = simpy.Store(_env, capacity=10)  # 10 is an arbitrary number

        _env.process(self.generate())
        _env.process(self.to_next_process())

    def generate(self):
        while True:
            while self.rec < self.num_parts:
                # 1. Generate a Part Object
                part = Job(self.model, env=self.env, job_type=self.job_type, id=self.rec)
                part.loc = self.name  # Update the part's current location

                # 2. Update the number of parts generates
                # so that the Source would stop after generating a certain amount of parts
                self.generated_parts.put(part)
                self.rec += 1

                # 3. Record through monitor class
                self.monitor.record(time=self.env.now, process=self.name, machine=None,
                                    part_name=part.name,
                                    event="Part" + str(self.name[-1]) + " Created")

                # 4. Print through Console (Optional)
                if CONSOLE_MODE:
                    print('-' * 15 + part.name + " Created" + '-' * 15)
                # 5. Proceed on IAT timeout
                # ! Handling an IAT value given as a string variable
                # If self.IAT is the string 'exponential(1)',
                # then this line will be equivalent to IAT = np.random.exponential(1)
                if type(self.IAT) is str:
                    IAT = eval('np.random.' + self.IAT)
                else:
                    IAT = self.IAT
                yield self.env.timeout(np.round(IAT))

    def to_next_process(self):
        while True:
            # 1. Get a part from the list of generated parts
            part = yield self.generated_parts.get()
            part.step += 1  # this makes part.step to 0
            self.monitor.record(self.env.now, self.name, machine=None,
                                part_name=part.name,
                                event="Routing Start")

            # 2. Check the next process
            # The machine is not assigned yet and is to be determined further, in the 'Process' class function
            next_process = part.op[part.step].process  # i.e. model['시운전']
            print('Next Process of ', part.name,' is:', part.op[part.step].process.name)
            # 3. Put the part into the in_part queue of the next process
            # This 'yield' enables handling Process of limited queue,
            # by pending the 'put' call until the process is available for a new part
            if CONSOLE_MODE:
                print(part.name, "is going to be put in ", next_process.name)
            yield next_process.in_buffer.put(part)
            part.loc = next_process.name
            # next_process.input_event.succeed()  # Enables detection of incoming part
            # next_process.input_event = simpy.Event(self.env)

            # 4. Record
            self.monitor.record(self.env.now, self.name, machine=None,
                                part_name=part.name,
                                event="Routing Finished")
            self.monitor.record(self.env.now, next_process.name, machine=None,
                                part_name=part.name, event="Part transferred from Source")


# endregion


if __name__ == "__main__":
    import sys
    from Process import *
    from Sink import Sink
    from Resource import Machine
    sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
    import quay

    env = simpy.Environment()
    monitor = Monitor(filepath)
    model = dict()



    NUM_MACHINE = len(quay.quay_list)
    for i, q in enumerate(quay.quay_list):
        model[q] = Machine(env, i,q)

    for j, p in enumerate(quay.process_list):
        model[p] = Process(env, p, model, monitor, _machine_order=None,
                                        capacity=1, in_buffer=12, out_buffer=12)

    NUM_JOB = len(quay.job_list)
    for i, j in enumerate(quay.job_list[:4]):
        model['Source' + str(i+1)] = Source(env, 'J-' + str(i+1), model, monitor,
                                      job_type=quay.job_list[i], IAT=IAT, num_parts=float('inf'))


    model['Sink'] = Sink(env, monitor)


    env.run(SIMUL_TIME)
    monitor.save_event()
