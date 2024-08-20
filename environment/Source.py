import simpy
import numpy as np
from environment.Part import Job, Operation
from environment.Monitor import Monitor
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(os.path.dirname(os.path.abspath(os.path.dirname(__file__))))))

# region Source
# source 클래스는 시뮬환경에서 부품을 생성하고 생성된 부품을 다음 공정으로 전송한다. 시스템의 출발지 역할을 모델링.
class Source(object):
    def __init__(self, _cfg, _env, _name, _model, _monitor, job_type, IAT='exponential(1)', num_parts=float('inf')):
        self.env = _env
        # _ 언더바는 임시 또는 지역 변수로 사용하거나 접근제한을 나타냄(비공개, 내부용)
        self.cfg = _cfg
        self.name = _name  # 해당 Source의 이름
        self.model = _model
        self.monitor = _monitor
        self.job_type = job_type  # Source가 생산하는 Part의 Job Type, 클래스 인자를 받을 예정
        self.IAT = IAT  # Source가 생성하는 Part의 IAT(jobtype을 통한 Part 생성)
        self.num_parts = num_parts  # Source가 생성하는 Part의 갯수

        self.rec = 0  # 현재까지 생성된 Part의 갯수를 기록하는 변수
        self.generated_parts = simpy.Store(_env, capacity=10)  # 10 is an arbitrary number
        # 생성된 부품을 임시로 저장하는 simpy.Store 객체

        _env.process(self.generate())
        _env.process(self.to_next_process())

    def generate(self):
        # IAT에 따라 반복적으로 부품 생성하고 이를 generated_parts에 저장. 생성된 각 부품은 'Job' 객체로 생성. 부품에 대한 정보와 생성 이벤트가 monitor에 의해 기록.
        while self.rec < self.num_parts:
            yield self.env.timeout(self.IAT)
            # 1. Generate a Part Object
            part = Job(self.model, env=self.env, job_type=self.job_type, id=self.rec)
            part.loc = self.name  # Update the part's current location

            if self.cfg.CONSOLE_MODE:
                print('-' * 15 + part.name + " Created" + '-' * 15)

            # 2. Update the number of parts generates
            # so that the Source would stop after generating a certain amount of parts
            self.generated_parts.put(part)
            # 여기에 저장
            self.rec += 1
            print("rec is " + str(self.rec))

            # 3. Record through monitor class
            self.monitor.record(time=self.env.now, process=self.name, machine=None,
                                part_name=part.name,
                                event="Part" + str(self.name[-1]) + " Created")

            # 4. Print through Console (Optional)

            # 5. Proceed on IAT timeout
            # ! Handling an IAT value given as a string variable
            # If self.IAT is the string 'exponential(1)',
            # then this line will be equivalent to IAT = np.random.exponential(1)
            # if type(self.IAT) is str:
            #     IAT = eval('np.random.' + self.IAT)
            #     # 문자열로 주어진 iat 값을 실행가능한 코드로 변환
            #     # self.IAT가 exponential(1)라는 값을 가진다면 np.random.exponential(1)이 됨.
            # else:
            #     IAT = self.IAT


    def to_next_process(self):
        # 생성된 부품을 처리하고 다음 공정으로 라우팅.
        # 부품은 generated_parts에서 추출되고 해당 부품의 다음 공정(next_process)로 전송(다음 공정의 in_buffer 입력버퍼로 이동)
        while True:
            # 1. Get a part from the list of generated parts
            part = yield self.generated_parts.get()
            print('OK?')
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

            if self.cfg.CONSOLE_MODE:
                print(part.name, "is going to be put in ", next_process.name)
            yield next_process.in_buffer.put(part)
            part.loc = next_process.name

            # 4. Record
            self.monitor.record(self.env.now, self.name, machine=None,
                                part_name=part.name,
                                event="Routing Finished")
            self.monitor.record(self.env.now, next_process.name, machine=None,
                                part_name=part.name, event="Part transferred from Source")


# endregion
