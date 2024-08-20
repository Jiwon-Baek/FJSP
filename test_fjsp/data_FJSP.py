"""
Data Hierarchy:

1. Job
Jobs are defined by their required processes and order.
Job information is stored as a list, with elements corresponding to jobs
(e.g., job_list[0] = ['Process1', 'Process4', 'Process5']).

2. Process (Operation)

Processes specify the type of work, compatible resources, and processing times.
Each operation is uniquely identified by combining job and process, denoted as 'Operation'
(e.g., Op1_3 for the third process of Job 1).

3. Operation

Processing times for each compatible machine are specified for each operation.
Example: Op3_1 has a processing time of 3 on Machine 1 and 7 on Machine 7.
"""
import simpy
from environment.Process import *
from environment.Source import Source
from environment.Sink import Sink
from environment.Resource import Machine
from environment.Monitor import Monitor
from postprocessing.PostProcessing import *
from visualization.Gantt import *
from visualization.GUI import GUI
from cfg_local import Configure
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
file_path = '.\FJSP sample data.xlsx'
df = pd.read_excel(file_path, sheet_name='Operation Information', header=0, index_col=None)
df_tpt = pd.read_excel(file_path, sheet_name='Transportation Information', header=0, index_col=0)
# header = 0: 첫번째 행을 컬럼 이름으로 사용, index_col=0: 어느 컬럼을 데이터프레임 인덱스로 사용할지
class JobType:
    def __init__(self, jobtype, process_order, machine_order, processing_time, release_date=None, due_date=None):
        self.jobtype = jobtype
        self.due_date = due_date
        self.release_date = release_date
        # a list of 10 elements (e.g. ['Process5','Process4',...,'Process9'])
        self.process_order = process_order

        # a list of 10 elements, each element notes the set of compatible machines as tuple
        # (e.g. [('M1','M2'), ('M2','M3'), ... , ('M7','M8','M9')] )
        self.machine_order = machine_order
        self.processing_time = processing_time
        self.num_process = len(process_order)
        """
        When the JobType object is created, it will be delivered to Source constructor
        """
job_list = []
machine_columns = [col for col in df.columns if "Machine" in col]
max_length = 0
u = df['Job_Name'].unique()
for i in range(len(u)):

    temp = df[df['Job_Name'] == "J-" + str(i)]
    length = temp.shape[0]
    if length > max_length:
        max_length = length
    op = temp["Operation_Name"].tolist()
    op_ = ['O-' + op[j][-1] for j in range(len(op))]


    machines = []
    machine = temp[machine_columns]
    indexes = temp.index.tolist()
    for l in indexes:
        temp1 = machine.loc[l][machine.loc[l] != 0].index.tolist()
        machines.append(temp1)
        # 이런 형태로 출력 machines = [['Machine0', 'Machine2'], ['Machine1', 'Machine2', 'Machine4'] ~ ]
    machine_ = [machine.loc[k].tolist() for k in indexes]
    pt = [[v for v in machine_[j] if v != 0] for j in range(len(op_))]
    release_date = temp.iloc[0]["Release_Date"]
    ddt = temp.iloc[0]["Due_Date"]


    job = JobType('J-'+str(i) , op_, machines, pt, release_date, ddt)
    job_list.append(job)

print(job_list)
# TODO: 동적으로 최대 OPERATION 개수 읽는 코드 짜야됨.
"""
temp = 0
    for i in job_list:
        if job.num_op > temp:
            temp=job.num_op        
"""

op_all = ['O-'+str(i) for i in range(max_length)]
machine_all = ['Machine'+str(i) for i in range(len(machine_columns))]
# 1. simpy 환경 생성
env = simpy.Environment()
# 2. 시뮬레이션 환경설정 객체 설정(경로, 실험 이름, job 개수 등 반복적으로 호출되는 것들)
cfg = Configure(num_job=len(job_list), num_machine=len(machine_columns))
# 3. monitor 객체 생성
monitor = Monitor(cfg.filepath)
# 4. model 구성
model = dict()
# 4-1. machine 객체 생성
for i in range(len(machine_columns)):
    model['Machine'+str(i)] = Machine(env, i,'Machine'+str(i))
# 4-2. process 객체 생성
for o in op_all:
    model[o] = Process(cfg, env, o, model, monitor, df_tpt)
# 4-3. job_type 객체 생성
for p in range(len(job_list)):
    model['Source' + str(p)] = Source(cfg, env, 'J' + str(p), model, monitor,
                                          job_type=job_list[p], IAT=job_list[p].release_date, num_parts=1)
# 4-4. sink 생성
model['Sink'] = Sink(cfg, env, monitor)

# machine_statistics 프린트
def print_machine_statistics(model, total_simulation_time):
    print(total_simulation_time)
    total_utilization = 0
    utilization_rates = []
    machine_names = []
    total_waiting_times = []
    total_transportation_time = 0

    for machine in model.values():
        if isinstance(machine, Machine):
            total_operations = len(machine.workingtime_log)
            total_utilization_time = sum(machine.workingtime_log)
            utilization_rate = (total_utilization_time / total_simulation_time) * 100 if total_simulation_time > 0 else 0
            # machine.total_waiting_time = sum([op.wait_time for op in machine.queue])

            total_utilization += utilization_rate
            utilization_rates.append(utilization_rate)
            machine_names.append(machine.name)
            total_waiting_times.append(machine.waiting_time)
            total_working_time = sum(machine.workingtime_log)
            total_transportation_time += machine.transportation_time

            print(f"{machine.name} statistics:")
            print(f"  Total operations: {total_operations}")
            print(f"  Total waiting time: {machine.waiting_time:.2f} hours")
            print(f"  Total utilization time: {total_utilization_time:.2f} hours")
            print(f"  Utilization rate: {utilization_rate:.2f}%")
            print(f"  Working time log: {machine.workingtime_log}")
            print(f"  Total working time: {total_working_time}")


    average_utilization = total_utilization / len(utilization_rates) if utilization_rates else 0
    std_dev_utilization = np.std(utilization_rates)

    print(f"Total transportation time: {total_transportation_time} hours")
    print(f"Average utilization rate: {average_utilization:.2f}%")
    print(f"Standard deviation of utilization rate: {std_dev_utilization:.2f}%")
    print(f"Total waiting times : {int(sum(total_waiting_times))} hours")

    # # 그래프 생성
    # plt.figure(figsize=(10, 6))
    # plt.bar(machine_names, utilization_rates, color='blue')
    # plt.xlabel('Machine')
    # plt.ylabel('Utilization Rate (%)')
    # plt.title('Machine Utilization Rates')
    # plt.ylim(0, 100)

    # Plotting
    sns.set(style="whitegrid")
    palette = sns.color_palette("pastel", len(machine_names))

    fig, ax1 = plt.subplots()

    ax1.bar(machine_names, utilization_rates, color=palette)
    ax1.set_xlabel('Machines')
    ax1.set_ylabel('Utilization Rate (%)')
    ax1.set_title('Machine Utilization Rates')
    plt.show()

# 5. 시뮬레이션 실행
env.run(5000)
# 6. 후처리를 위한 이벤트 로그 저장
monitor.save_event()

# In case of the situation where termination of the simulation greatly affects the machine utilization time,
# it is necessary to terminate all the process at (SIMUL_TIME -1) and add up the process time to all machines

machine_log = read_machine_log(cfg.filepath)
# 7. 간트차트 출력
gantt = Gantt(cfg, machine_log, len(machine_log), printmode=True, writemode=True)
# gui = GUI(gantt)
print()

total_simulation_time = model['Sink'].last_arrival # 끝나는 시간
utilization_rate = (total_utilization_time / total_simulation_time) * 100
# 기계 통계 출력
print_machine_statistics(model, total_simulation_time)