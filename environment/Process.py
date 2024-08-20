import simpy
import random
random.seed(42)
import sys
# 파이썬 라이브러리가 설치되어 있는 디렉터리를 확인할 수 있다.
import os
#
import numpy as np


sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))
# sys.path: 파이썬 라이브러리가 설치되어 있는 디렉터리를 확인할 수 있다.
# __file__: 현재 실행중인 스크립트의 경로를 담고 있는 특수 변수.
# abspath: 절대 경로를 반환 / dirname: 주어진 경로의 디렉토리 이름 반환. / dirname 3번 사용해서 세단계 상위 디렉토리 경로 반환
# sys.path:에 새로운 경로 추가: 이로써 해당 경로에 있는 파이썬 모듈 import 할 수 있게 됨.

from environment.Monitor import *

# from config import *
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))


class Process(object):
    def __init__(self, _cfg, _env, _name, _model, _monitor, _transportation_times):
        # 프로세스 객체의 초기화. 필수 입력 데이터로 시뮬레이션 환경, 공정 이름, 모델, 모니터 객체, 설정파일.
        # input data
        self.env = _env
        self.name = _name  # 해당 프로세스의 이름
        self.model = _model
        # 모델 데이터
        self.monitor = _monitor
        # 이벤트 기록을 위한 모니터 객체
        self.cfg = _cfg
        # 설정 데이터, 구성 정보를 담고 있음.
        self.tpt = _transportation_times
        self.in_buffer = simpy.FilterStore(_env, capacity=float('inf')) # 입력 버퍼
        self.out_buffer = simpy.FilterStore(_env, capacity=float('inf')) # 출력 버퍼
        # simpy.FilterStore: 필터링 기능을 제공하는 저장소, 특정 조건 만족하는 항목만 처리. / inf: 버퍼크기 무한

        self.work_waiting = [self.env.event() for i in range(self.cfg.num_job)]
        # 작업 대기 이벤트 생성, 작업의 시작을 제어할 수 있음.
        """ 
        각 작업이 시작되기 전에 대기해야하는 이벤트들을 저장하는 리스트.
        이 리스트의 길이는 cfg.num_job과 같음. 각 요소는 event로 생성된 이벤트 객체.
        """


        # 시뮬레이션 환경에 프로세스 등록
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
        # 밑에 run 함수에서 불러옴.

        # 특정 부품에 대한 실제 작업을 수행. 선택된 기계에서 부품을 처리하는 로직을 담고 있으며, 작업시작과 완료 시 모니터에 이벤트 기록.
        # 작업 선행조건 만족시까지 대기 후, 기계 사용가능 여부 확인하고 작업 시작, 완료되면 사용된 기계 상태 업데이트 후 부품을 출력 버퍼로 이동.
        # 1. Check if former operations are all finished & requirements are satisfied
        operation = part.op[part.step]
        # op 리스트 안에 각 operation에 대한 모든 정보 담겨 있음.

        # 작업이 큐에 들어가는 시간 기록
        operation.queue_entry_time = self.env.now

        yield operation.requirements
        # 선행조건이 충족되길 기다림.
        yield machine.availability.put('using')
        # 기계의 사용 가능 상태를 체크하고 사용 상태로 변경

        # 작업이 큐에서 나오는 시간 기록 및 대기 시간 계산
        wait_end_time = self.env.now
        machine.operation_count += 1  # 추가: 처리한 operation 수 증가
        wait_time = wait_end_time - operation.queue_entry_time
        print(f"{machine.name}의 {machine.operation_count}번째 wait time은 {wait_time}이다.")
        machine.total_waiting_time += wait_time

        # tpt 반영
        if part.step > 0:
            prev_machine = part.op[part.step - 1].machine_determined.name
            trans_time = self.tpt.loc[prev_machine, machine.name]
            # loc: 특정 행열 선택.
            print(f"Moving from {prev_machine} to {machine.name}. It will take {trans_time} hours.")
            yield self.env.timeout(trans_time)
            machine.transportation_time += trans_time
        # 2. Update machine status
        # 다른 class object들에게 알려주기 위해 상태와 가장 빠른 종료시간을 기록
        # TODO : work()를 발생시킬 때, 해당 machine의 내부 변수에
        #  이만큼의 operation이 대기중이라는 사실을 기록해서 다른 class에서도 참조하도록 해야 하지 않을까?
        machine.status = 'Working'
        # 기계 상태 업데이트
        machine.turn_idle = self.env.now + pt
        # 작업 완료 예정시간 계산 / 이제 일을 시작하니까 지금시점부터 pt 더하기
        machine.queue.remove(operation)
        # 기계 큐에서 작업 제거 / 지금 일을 하니까.

        # 3. Proceed & Record through console
        self.monitor.record(self.env.now, self.name, machine=machine.name,
                            part_name=part.name, event="Started") # 작업 시작 기록

        if self.cfg.CONSOLE_MODE:
            monitor_console(self.env.now, part, self.cfg.OBJECT, "Started on")

        yield self.env.timeout(pt)
        # 작업시간동안 대기. process time
        self.monitor.record(self.env.now, self.name, machine=machine.name,
                            part_name=part.name, event="Finished") # 작업 완료 기록
        if self.cfg.CONSOLE_MODE:
            monitor_console(self.env.now, part, self.cfg.OBJECT, "Finished on")

        machine.util_time += pt
        # 기계 사용시간 누적
        machine.workingtime_log.append(pt)
        machine.waiting_time += self.env.now - part.start_waiting_time
        # 대기시간 기록

        # 4. Send(route) to the out_part queue for routing and update the machine availability
        yield self.out_buffer.put(part)
        # 완료된 부품을 출력버퍼로 이동
        yield machine.availability.get()
        # 기계 사용 상태 해체
        machine.status = 'Idle'
        # 기계 상태를 유휴 상태로 변경

    def run(self):
        # 공정의 주 실행 루프를 정의. 무한푸르 통해 지속적으로 작업 받아 처리하고 적절한 기계를 선택하여 작업 실행.
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
            # 입력 버퍼에서 작업 부품 가져옴.
            part.start_waiting_time = self.env.now
            # 부품이 큐에 들어온 시간 기록.

            ############### 2. Machine의 결정
            # TODO : call agent for selecting a machine
            operation = part.op[part.step]
            # operation.queue_entry_time = self.env.now
            # 현재 작업 단계 가져옴.
            if isinstance(operation.machine_available, list):  # 만약 여러 machine에서 작업 가능한 operation이라면
                # machine, pt = self.heuristic_LIT(operation)
                # machine, pt = self.heuristic_LUT(operation)
                # machine, pt = self.heuristic_SPT(operation)
                # machine, pt = self.heuristic_LPT(operation)
                # machine, pt = self.heuristic_LOR(operation)
                machine, pt = self.heuristic_MOR(operation)


                # machine, pt = self.heuristic_MWR(operation)
                # machine, pt = self.heuristic_LWR(operation)
                # machine, pt = self.heuristic_FJSP(operation)
                # 다양한 기계에서 작업가능한 경우 휴리스틱 FJSP 함수로 최적 기계 선택

            else:  # 만약 단일 기계에서만 작업 가능한 operation이라면
                machine, pt = self.heuristic_JSSP(operation)

            # 결정된 사항을 기록해 둠
            operation.machine_determined = machine
            operation.process_time_determined = pt
            machine.queue.append(operation)
            # 선택된 기계의 큐에 작업 추가.

            print('%d \t%s have %d operations in queue... turning idle at %d... \tfinish working at %d' %
                  (self.env.now, machine.name, len(machine.queue), machine.turn_idle, machine.expected_turn_idle()))

            ############### 3. work() 인스턴스 생성 / 작업이 실제로 기계에서 작업시작.
            self.env.process(self.work(part, machine, pt))



    def heuristic_LIT(self, operation):
        machine_list = operation.machine_available
        least_idle_time = min(len(m.queue) for m in machine_list)
        candidates = [m for m in machine_list if len(m.queue) == least_idle_time]
        least_idle_machine = random.choice(candidates)
        process_time = operation.process_time[machine_list.index(least_idle_machine)]
        return least_idle_machine, process_time

    def heuristic_LUT(self, operation):
        machine_list = operation.machine_available
        least_util_time = min(m.util_time for m in machine_list)
        candidates = [m for m in machine_list if m.util_time == least_util_time]
        least_util_machine = random.choice(candidates)
        process_time = operation.process_time[machine_list.index(least_util_machine)]
        return least_util_machine, process_time

    def heuristic_SPT(self, operation):
        machine_list = operation.machine_available
        min_process_time = min(operation.process_time)
        candidates = [m for i, m in enumerate(machine_list) if operation.process_time[i] == min_process_time]
        selected_machine = random.choice(candidates)
        return selected_machine, min_process_time

    def heuristic_LPT(self, operation):
        machine_list = operation.machine_available
        max_process_time = max(operation.process_time)
        candidates = [m for i, m in enumerate(machine_list) if operation.process_time[i] == max_process_time]
        selected_machine = random.choice(candidates)
        return selected_machine, max_process_time

    def heuristic_MOR(self, operation):
        machine_list = operation.machine_available
        max_operations_remaining = max(len(m.queue) for m in machine_list)
        candidates = [m for m in machine_list if len(m.queue) == max_operations_remaining]
        most_ops_remaining_machine = random.choice(candidates)
        process_time = operation.process_time[machine_list.index(most_ops_remaining_machine)]
        return most_ops_remaining_machine, process_time

    def heuristic_LOR(self, operation):
        machine_list = operation.machine_available
        least_operations_remaining = min(len(m.queue) for m in machine_list)
        candidates = [m for m in machine_list if len(m.queue) == least_operations_remaining]
        least_ops_remaining_machine = random.choice(candidates)
        process_time = operation.process_time[machine_list.index(least_ops_remaining_machine)]
        return least_ops_remaining_machine, process_time

    # def heuristic_LIT(self, operation):
    #     machine_list = operation.machine_available
    #     least_idle_machine = min(machine_list, key=lambda m: m.expected_turn_idle())
    #     process_time = operation.process_time[machine_list.index(least_idle_machine)]
    #     return least_idle_machine, process_time
    #
    # # 2. LUT (Least Utilization Time)
    # def heuristic_LUT(self, operation):
    #     machine_list = operation.machine_available
    #     least_util_machine = min(machine_list, key=lambda m: m.util_time)
    #     process_time = operation.process_time[machine_list.index(least_util_machine)]
    #     return least_util_machine, process_time
    #
    # # 3. MOR (Most Operations Remaining): 머신 큐에 작업 가장 많이 있는 머신 우선.
    # def heuristic_MOR(self, operation):
    #     machine_list = operation.machine_available
    #     most_ops_remaining_machine = max(machine_list, key=lambda m: len(m.queue))
    #     process_time = operation.process_time[machine_list.index(most_ops_remaining_machine)]
    #     return most_ops_remaining_machine, process_time
    #
    # # 4. MWR (Most Waiting Resources)
    # def heuristic_MWR(self, operation):
    #     machine_list = operation.machine_available
    #     most_waiting_resources_machine = max(machine_list, key=lambda m: len(m.availability.items))
    #     process_time = operation.process_time[machine_list.index(most_waiting_resources_machine)]
    #     return most_waiting_resources_machine, process_time
    #
    # def heuristic_LOR(self, operation):
    #     machine_list = operation.machine_available
    #     least_ops_remaining_machine = min(machine_list, key=lambda m: len(m.queue))
    #     process_time = operation.process_time[machine_list.index(least_ops_remaining_machine)]
    #     return least_ops_remaining_machine, process_time
    #
    # def heuristic_LWR(self, operation):
    #     machine_list = operation.machine_available
    #     least_waiting_resources_machine = min(machine_list, key=lambda m: len(m.availability.items))
    #     process_time = operation.process_time[machine_list.index(least_waiting_resources_machine)]
    #     return least_waiting_resources_machine, process_time
    #
    # def heuristic_FJSP_SPT(self, operation):
    #     machine_list = operation.machine_available
    #     pt_list = operation.process_time
    #     pt_list_min_index = pt_list.index(min(pt_list))
    #     machine = machine_list[pt_list_min_index]
    #
    #     return machine, min(pt_list)
    #
    # def heuristic_FJSP_LPT(self, operation):
    #     machine_list = operation.machine_available
    #     pt_list = operation.process_time
    #     pt_list_max_index = pt_list.index(max(pt_list))
    #     machine = machine_list[pt_list_max_index]
    #
    #     return machine, max(pt_list)

    def heuristic_FJSP(self, operation):
        # compatible machine list
        machine_list = operation.machine_available
        # 사용 가능한 기계 목록 가져옴.
        # compatible machine들의 현황을 파악해서 가장 idle한 machine을 지정

        # Remark : 그런데 학습에 따라서 현재 대기시간이 많이 남은 machine이더라도 그게 좋다고 판단되면 선택할 수 있어야 하지 않나?
        # TODO : 현재는 고의로 idle하게 machine을 남겨두는 것이 불가능함(non-delay) -> 수정 필요

        remaining_time = []
        # 기계 대기시간을 평가하여 가장 빠르게 사용가능한 기계 목록 가져옴.
        for m in machine_list:
            if m.status == 'Idle':
                remaining_time.append(0)
                # 기계 쉬는 중이면 즉시 선택
            else:
                remaining_time.append(m.expected_turn_idle() - self.env.now)
                # 그렇지 않으면 남은 가동시간 계산

                # remaining_time.append(m.turn_idle - self.env.now)
        # index of the machine with the least remaining time
        least_remaining = np.argmin(remaining_time)
        # 남은 가동 시간이 가장 짧은 기계를 선택. "index"
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
            # 출력 버퍼에서 부품 가져옴.
            print('Part Arrived:', part.name)
            if part.step != part.num_process - 1:  # for operation 0,1,2,3 -> part.step = 1,2,3,4
                # 모든 공정 완료되지 않았다면 다음 공정으로 진행
                part.step += 1
                part.op[part.step].requirements.succeed()
                next_process = part.op[part.step].process  # i.e. model['Process0']
                # 다음 공정의 요구사항을 충족시키면 다음 공정을 가져옴.

                # The machine is not assigned yet (to be determined further)
                yield next_process.in_buffer.put(part)
                # 다음 프로세스의 입력 버퍼로 부품 이동.
                part.loc = next_process.name
                # 부품의 현재 위치 업데이트
            else:
                self.model['Sink'].put(part)
                # 모든 공정 완료시 최종 목적지로 부품 이동.
