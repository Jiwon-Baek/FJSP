import pandas as pd

# from config import CONSOLE_MODE

# region Monitor
class Monitor(object):
    def __init__(self, filepath):
        self.filepath = filepath
        self.time = list()
        self.event = list()
        self.part = list()
        self.process_name = list()
        self.machine_name = list()

    def record(self, time, process, machine, part_name=None, event=None):
        self.time.append(time)
        self.event.append(event)
        self.part.append(part_name)
        self.process_name.append(process)
        self.machine_name.append(machine)

    def save_event(self):
        event = pd.DataFrame(columns=['Time', 'Event', 'Part', 'Process', 'Machine'])
        event['Time'] = self.time
        event['Event'] = self.event
        event['Part'] = self.part
        event['Process'] = self.process_name
        event['Machine'] = self.machine_name
        event.to_csv(self.filepath)
        return event

# endregion

# 간단한 부품과 공정 예시
class Part:
    def __init__(self):
        self.step = 0
        self.op = [{
            'name': 'Drilling',
            'machine': 'Drill Press',
            'machine_determined': {'name': 'Drill Press 1'},
            'machine_list': 1,
            'part_name': 'Part0_0'
        }]

# Monitor 인스턴스 생성 및 이벤트 기록
monitor = Monitor('events.csv')
monitor.record(time="10:00", process="Start", machine="Drill Press", part_name="Part0_0", event="Begin Operation")
monitor.record(time="10:30", process="Check", machine="Drill Press", part_name="Part0_0", event="Mid Operation")
monitor.record(time="11:00", process="End", machine="Drill Press", part_name="Part0_0", event="End Operation")
monitor.save_event()

# 이벤트를 콘솔에 출력
def monitor_console(time, part, object='Entire Process', command=''):
    operation = part.op[part.step]
    command = " "+command+" "
    if object == 'Single Part':
        print(str(time), '\t', operation.name, command, operation.machine)
    elif object == 'Single Job':
        if operation.part_name == 'Part0_0':
            print(str(time), '\t', operation.name, command, operation.machine)
    elif object == 'Entire Process':
        print(str(time), '\t', operation.name, command, operation.machine_determined['name'])
    elif object == 'Machine':
        print_by_machine(time, part)

def print_by_machine(env, part):
    if part.op[part.step].machine_list == 0:
        print(str(env.now), '\t\t\t\t', str(part.op[part.step].name))
    elif part.op[part.step].machine_list == 1:
        print(str(env.now), '\t\t\t\t\t\t\t', str(part.op[part.step].name))
    elif part.op[part.step].machine_list == 2:
        print(str(env.now), '\t\t\t\t\t\t\t\t\t\t', str(part.op[part.step].name))
    elif part.op[part.step].machine_list == 3:
        print(str(env.now), '\t\t\t\t\t\t\t\t\t\t\t\t\t', str(part.op[part.step].name))
    elif part.op[part.step].machine_list == 4:
        print(str(env.now), '\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t\t', str(part.op[part.step].name))
    else:
        print()

# 가상의 시간과 부품 객체를 사용하여 함수를 시험
part_example = Part()
monitor_console("10:00", part_example, "Entire Process", "Operation Started")