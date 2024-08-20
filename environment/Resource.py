import simpy

class Machine(object):
    def __init__(self, env, id, name):
        # 기계 고유 식별자, 이름, 기계 용량(한번에 하나의 작업 처리), 가용성, 상태 초기화
        self.env = env
        self.id = id
        self.name = name
        self.capacity = 1
        self.availability = simpy.Store(env, capacity=self.capacity)
        self.status = 'Idle'  # 'Working' or 'Idle'

        # 다음 Idle 상태가 되는 시점을 기록
        # 외부에서 참조해서 특정 시점에 가장 빠르게 idle해지는 machine을 찾아내는 데 활용함
        self.turn_idle = 0

        # Process.work() 발생으로 인해 결정된 Machine의 대기열 리스트
        # job name을 넣고, 완료되면 제거
        # 나중에 self.turn_idle과 함께 해당 machine에 operation이 얼마나 밀려 있는지를 나타내는 지표로 활용할 예정임
        self.queue = []

        # 기계의 작업시간 로그, 기계의 총 사용 시간
        self.workingtime_log = []
        self.util_time = 0.0
        # 대기 시간 기록
        self.waiting_time = 0.0
        self.total_waiting_time = 0
        self.operation_count = 0  # 추가: 처리한 operation 수를 저장하는 변수
        self.transportation_time = 0 # 운송시간 추적

    def expected_turn_idle(self):
        # 기계가 다음 유휴 상태가 될 예상 시간 계산.
        eti = self.turn_idle
        for op in self.queue:
            eti += op.process_time_determined
            # turn idle 값에 대기열 있는 모든 작업의 처리시간을 더하여 계산됨.
        return eti
class Worker(object):
    def __init__(self, env, id):
        self.env = env
        self.id = id
        self.capacity = 1
        # 작업자가 동시에 처리할 수 있는 작업의 수(1), 가용성.
        self.availability = simpy.Store(env, capacity=self.capacity)
        # 작업시간 로그, 작업자의 총 사용시간
        self.workingtime_log = []
        self.util_time = 0.0

class Jig(object):
    def __init__(self, env, id):
        self.env = env
        self.id = id
        self.capacity = 1
        self.availability = simpy.Store(env, capacity=self.capacity)
        self.workingtime_log = []
        self.util_time = 0.0
