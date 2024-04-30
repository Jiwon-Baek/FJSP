import simpy
import sys
import os
import numpy as np

sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))

from environment.Monitor import *

# from config import *
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))


class Process(object):
    def __init__(self, _cfg, _env, _name, _model, _monitor):
        # input data
        self.env = _env
        self.name = _name  # 해당 프로세스의 이름
        self.model = _model
        self.monitor = _monitor
        self.cfg = _cfg

        self.in_buffer = simpy.FilterStore(_env, capacity=float('inf'))
        self.out_buffer = simpy.FilterStore(_env, capacity=float('inf'))

        self.work_waiting = [self.env.event() for i in range(self.cfg.num_job)]

        # get run functions in class
        _env.process(self.run())
        _env.process(self.to_next_process())

    """
    Class Description
    Process.run() : 작업 하나를 골라서 env.process()에 work를 추가시킴
    Process.work() : machine의 사용권을 얻고, timeout이 일어나는 부분
    Process.to_next_process() : 다음 process로 전달
    """

    def work(self, part, machine, pt):
        # 1. Check if former operations are all finished & requirements are satisfied
        operation = part.op[part.step]
        yield operation.requirements
        yield machine.availability.put('using')

        # 2. Update machine status
        # 다른 class object들에게 알려주기 위해 상태와 가장 빠른 종료시간을 기록
        # TODO : work()를 발생시킬 때, 해당 machine의 내부 변수에
        #  이만큼의 operation이 대기중이라는 사실을 기록해서 다른 class에서도 참조하도록 해야 하지 않을까?
        machine.status = 'Working'
        machine.turn_idle = self.env.now + pt
        machine.queue.remove(operation)

        # 3. Proceed & Record through console
        self.monitor.record(self.env.now, self.name, machine=machine.name,
                            part_name=part.name, event="Started")
        if self.cfg.CONSOLE_MODE:
            monitor_console(self.env.now, part, self.cfg.OBJECT, "Started on")

        yield self.env.timeout(pt)
        self.monitor.record(self.env.now, self.name, machine=machine.name,
                            part_name=part.name, event="Finished")
        if self.cfg.CONSOLE_MODE:
            monitor_console(self.env.now, part, self.cfg.OBJECT, "Finished on")

        machine.util_time += pt

        # 4. Send(route) to the out_part queue for routing and update the machine availability
        yield self.out_buffer.put(part)
        yield machine.availability.get()
        machine.status = 'Idle'

    def run(self):
        """
        [생각해 볼 만한 이슈]
        1. 현재는 scheduler가 아무 job도 고르지 않기를 선택하는 경우에 대한 대응이 불가능함

        2. 현재는 work()를 발생시키는 시점이 실제 해당 job의 operation의 실행 시점과 다름.
        따라서, machine의 availability 등을 확인하고 dispatching하는 것이 불가능함.
        (추가) 이를 고려하기 위해 idle한 machine이 있는 job들만을 대상으로
        work()를 발생시키는 것을 고려해 볼 수 있음

        2-1. 위의 방법대로 했을 때, idle한 machine이 있다는 것을 근거로 work()를 발생시킨다는 것은
        사실상 machine selection의 자유도를 주지 않는 것과 같은 결과를 낳을 수 있음.
        (해결책) 일단 machine buffer에 넣어놓고 나중에 machine이 결정하도록 해도 된다. (=>multi-agent)
        (안벽문제의 경우 하루 delay되는 비용이 커서 machine 선택에 자유도를 부여하지 않고
        그냥 일단 들어가게끔 했음.)

        2-2. 궁극적으로는 이런 점까지 고려해서 '적절한 job을 잘 고르는 것'을 agent가 학습하도록 할 수도 있음

        2-3. 아니면 self.run()의 제어를 while True에 맡기는 것이 아니라 env.step()으로 제어해 가면서
        machine이 idle해지는 유의미한 timestep에 work()를 발생시키도록 하는 방법을 생각해볼 수 있음.
        이때 동일 timestep에 벌어지는 사건들에 우선순위를 두어 제어해야 한다면, env._queue() 등을 사용할 수 있다.

        3. 만약에 Process1과 Process2에서 모두 쓸 수 있는 machine이 idle해진 상황이라면,
        두 Process의 run()에서 각자 동일한 이유로 하나의 machine에 2개의 job이 줄을 서게 될 수도 있음.
        => 비효율성 발생 가능

        4. 아예 다른 방법은, Machine이 idle해질 때마다, 가능한 모든 process와 그에 속한 queue에
        대기중인 job들을 보고 고르게 하는 것임. (JSSP_V1, event queue 방법)
        """

        while True:
            ############### 1. Job의 결정
            # TODO : call agent for selecting a part
            part = yield self.in_buffer.get()

            ############### 2. Machine의 결정
            # TODO : call agent for selecting a machine
            operation = part.op[part.step]
            if isinstance(operation.machine_available, list):  # 만약 여러 machine에서 작업 가능한 operation이라면
                machine, pt = self.heuristic_FJSP(operation)

            else:  # 만약 단일 기계에서만 작업 가능한 operation이라면
                machine, pt = self.heuristic_JSSP(operation)

            # 결정된 사항을 기록해 둠
            operation.machine_determined = machine
            operation.process_time_determined = pt
            machine.queue.append(operation)

            # print('%d \t%s have %d operations in queue... turning idle at %d... \tfinish working at %d' %
            #       (self.env.now, machine.name, len(machine.queue), machine.turn_idle, machine.expected_turn_idle()))

            ############### 3. work() 인스턴스 생성
            self.env.process(self.work(part, machine, pt))

    def heuristic_FJSP(self, operation):
        # compatible machine list
        machine_list = operation.machine_available
        # compatible machine들의 현황을 파악해서 가장 idle한 machine을 지정

        # Remark : 그런데 학습에 따라서 현재 대기시간이 많이 남은 machine이더라도 그게 좋다고 판단되면 선택할 수 있어야 하지 않나?
        # TODO : 현재는 고의로 idle하게 machine을 남겨두는 것이 불가능함(non-delay) -> 수정 필요

        remaining_time = []
        for m in machine_list:
            if m.status == 'Idle':
                remaining_time.append(0)
            else:
                remaining_time.append(m.expected_turn_idle() - self.env.now)
                # remaining_time.append(m.turn_idle - self.env.now)
        # index of the machine with the least remaining time
        least_remaining = np.argmin(remaining_time)
        # TODO : 만약에 argmin인 값이 둘 이상일 때 (예를 들면 idle한 machine이 둘 이상일 때) 어떤 것을 선택할지 결정해야 함

        machine = machine_list[least_remaining]

        # process time on the certain machine이 list로 주어진 경우 vs. 단일 값으로 주어진 경우
        if isinstance(operation.process_time, list):
            process_time = operation.process_time[least_remaining]
        else:
            process_time = operation.process_time
        return machine, process_time

    def heuristic_JSSP(self, operation):
        machine = operation.machine_available
        process_time = operation.process_time

        # record the dispatching result
        operation.machine_determined = machine
        operation.process_time_determined = process_time
        return machine, process_time

    def to_next_process(self):
        while True:
            part = yield self.out_buffer.get()
            print('Part Arrived:', part.name)
            if part.step != part.num_process - 1:  # for operation 0,1,2,3 -> part.step = 1,2,3,4
                part.step += 1
                part.op[part.step].requirements.succeed()
                next_process = part.op[part.step].process  # i.e. model['Process0']
                # The machine is not assigned yet (to be determined further)
                yield next_process.in_buffer.put(part)
                part.loc = next_process.name
            else:
                self.model['Sink'].put(part)
