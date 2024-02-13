import simpy
from config import CONSOLE_MODE

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
        self.turn_idle = None

        self.workingtime_log = []
        self.util_time = 0.0


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
