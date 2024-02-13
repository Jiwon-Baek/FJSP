import pandas as pd
from config import CONSOLE_MODE

# region Monitor
class Monitor(object):
    def __init__(self, filepath):
        self.filepath = filepath  ## Event tracer 저장 경로
        self.time = list()
        self.event = list()
        self.part = list()
        self.process_name = list()
        self.machine_name = list()

    def record(self, time, process, machine, part_name=None, event=None):
        self.time.append(time)
        self.event.append(event)
        self.part.append(part_name)  # string
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

def monitor_console(time, part, object='Entire Process', command=''):
    """
    console_mode : boolean
    object : 'single part' for default
    """
    if CONSOLE_MODE:
        operation = part.op[part.step]
        command = " "+command+" "
        if object == 'Single Part':
            print(str(time), '\t', operation.name, command,end='')
            print(operation.machine)
        elif object == 'Single Job':
            if operation.part_name == 'Part0_0':
                print(str(time), '\t', operation.name, command,end='')
            print(operation.machine)
        elif object == 'Entire Process':
            print(str(time), '\t', operation.name, command, operation.machine_determined.name)
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
