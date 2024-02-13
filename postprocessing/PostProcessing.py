import pandas as pd
from collections import OrderedDict, defaultdict
from config import *
NUM_MACHINE = 28

# TODO : read_machine_log로 이름 변경
def read_machine_log(_filepath):
    df = pd.read_csv(_filepath)
    df = df.drop(df.columns[0], axis=1)
    # Filter 'Started' and 'Finished' events
    df_started = df[df['Event'] == 'Started'].drop(['Event', 'Process'], axis=1).reset_index(drop=True)
    df_finished = df[df['Event'] == 'Finished'].drop(['Event', 'Process'], axis=1).reset_index(drop=True)

    machine_list = df['Machine'].unique()
    machine_start = []
    machine_finish = []
    for i in range(len(machine_list)):
        machine_start.append(df_started[(df_started['Machine'] == machine_list[i])])
        machine_finish.append(df_finished[(df_finished['Machine'] == machine_list[i])])

        machine_start[i].reset_index(drop=True, inplace=True)
        machine_finish[i].reset_index(drop=True, inplace=True)
    data = []

    for i in range(len(machine_list)):
        for j in range(len(machine_finish[i])):
            temp = {'Machine': machine_list[i],
                    'Job': machine_start[i].loc[j, 'Part'],
                    'Start': int(machine_start[i].iloc[j, 0]),
                    'Finish': int(machine_finish[i].iloc[j, 0]),
                    'Delta': int(machine_finish[i].iloc[j, 0] - machine_start[i].iloc[j, 0])}
            data.append(temp)

    data = pd.DataFrame(data)
    data = data.sort_values(by=['Start'])
    data.reset_index(drop=True, inplace=True)
    data.to_csv(_filepath.split('.')[0]+'_machine_log.csv')
    return data
