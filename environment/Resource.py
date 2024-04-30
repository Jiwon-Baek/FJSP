import simpy

class Machine(object):
    def __init__(self, env, id,name):
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

        self.workingtime_log = []
        self.util_time = 0.0
    def expected_turn_idle(self):
        eti = self.turn_idle
        for op in self.queue:
            eti += op.process_time_determined

        return eti



class Worker(object):
    def __init__(self, env, id):
        self.env = env
        self.id = id
        self.capacity = 1
        self.availability = simpy.Store(env, capacity=self.capacity)
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
