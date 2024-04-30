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
        self.work_queue = simpy.FilterStore(_env, capacity=float('inf'))
        self.out_buffer = simpy.FilterStore(_env, capacity=float('inf'))

        self.work_waiting = [self.env.event() for i in range(self.cfg.num_job)]

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
            # TODO : Agent 호출

            """
            Remark : routing은 자체 결정하게 따로 냅둬도 괜찮을 것 같다. 
            (tuple 형태로 둘다 agent가 전달하는 게 아니라)
            => multi agent로의 확장이 가능해진다
            
            """
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
        if self.cfg.CONSOLE_MODE :
            monitor_console(self.env.now, part, self.cfg.OBJECT, "Started on")

        yield self.env.timeout(pt)
        self.monitor.record(self.env.now, self.name, machine=machine.name,
                            part_name=part.name, event="Finished")
        if self.cfg.CONSOLE_MODE :
            monitor_console(self.env.now, part, self.cfg.OBJECT, "Finished on")

        machine.util_time += pt

        # 4. Send(route) to the out_part queue for routing and update the machine availability
        yield self.out_buffer.put(part)
        yield machine.availability.get()
        machine.status = 'Idle'

    def dispatching(self):
        """ 다음으로 진행할 작업을 결정하는 부분을 분리함 """

        """
        만약 이 부분에서 agent가 distributor 를 calling 한다면
        1. 일단 input event를 감지하기 위한 simpy.env.Event()가 필요
        2. input event가 감지되면, calling event 발생 
        3. scheduler는 calling을 감지하고 여러가지 index 중 하나를 반환 
        3-2. 이때 아예 아무것도 반환하지 않기를 선택할 수도 있음. 그러면 scheduler는 계속 다음 calling event 받도록 하고
             여기에서 yield를 걸어서 다음 input event가 발생할 때까지 기다려야 함.
             => self.dispatching()을 env.process()에 넣을 게 아닌 것 같은데?

        4. 그리고 지금은 input event 기준이라서 실제 process의 idle함과는 관련이 없음
            시간을 계속해서 tracking 해가면서 끝나자마자 다른 job 넣고, ... 이런게 불가능함
            지금은 job이 들어오자 마자 이걸 지금 당장 할건지 말건지 아니면 당장 아무것도 안하고 기다릴지를 결정하는 구조임
            => machine이 idle해지는 시점에 KPI를 구해서 그걸 scheduling에 활용하는 게 불가능함
        5. 결론) work()을 뭔가 while true가 아니라 machine이 idle해지는 순간마다 발동하도록 연계해야 할 것 같음
        
        근데 그렇게 했을 때 문제) 만약에 Process1과 Process2에서 모두 쓸 수 있는 machine이 idle해진 상황에,
        두개의 calling event가 발생해 버리면 각 Process 입장에서는 이걸 모르고 각자 dispatching할 작업을 선택할텐데?
        
        """
        # fixme : 가용 가능한 machine이 없으면 애초에 work()를 발생시키지 않는 쪽으로 제어

        """
        그리고 사실상 machine을 골라주는 건 work()에서 할 예정이었는데, 여기서 지금 machine이 idle해지자마자 job을 보내면 
        (사실상 별다른 선택지가 없는 상황에서 job을 보내면) machine은 선택할 필요가 없이 자동으로 지정되는 것과 같음

        => (해결책) 일단 machine buffer에 넣어놓고 나중에 machine이 결정하도록 해도 된다.
        (안벽문제의 경우 하루 delay되는 비용이 커서 machine 선택에 자유도를 부여하지 않고 그냥 일단 들어가게끔 했음.)
        
        Machine이 idle해질 때마다, 가능한 모든 process와 그에 속한 queue에 대기중인 job들을 보고 고르게 하기 -> 가능성 있음
        그렇다면 현재의 dispatching - work로 이원화해놓은 부분이 불필요해짐.
        
        => (해결책2) env._queue 에서 특정 시점에 실행되는 모든 event를 list로 관리할 수 있게끔 해놨음
        ====> 같은 시점에 일어나는 여러 일들을 다 env.step()으로 실행시키고 나서 의사결정을 하면 됨
        
        => Process_v2 파일로 구현할 예정
        """

        while True:
            # print(self.name,'\t','Waiting for next arrival')
            # print(self.name,'\t','A new part arrived')

            # 갈 곳이 있는 part 대상으로만 딱히 하지 않아도 알아서 나중에 학습하게 됨
            # TODO : call agent for selecting a part

            part_ready = yield self.in_buffer.get()

            # TODO : call agent for selecting a machine
            # 아니면 휴리스틱으로 결정해 주던가

            # execute work()

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
            # Remark : 그런데 학습에 따라서 현재 대기시간이 많이 남은 machine이더라도 그게 좋다고 판단되면 선택할 수 있어야 하지 않나?
            # TODO : 현재는 고의로 idle하게 machine을 남겨두는 것이 불가능함 -> 수정 필요

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

        else:
            # if the compatible machine is determined and not given as list
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

