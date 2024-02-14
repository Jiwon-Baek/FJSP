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

import pandas as pd
import os

# Read the Excel file
file_path = '.\quay.xlsx'
df_ship = pd.read_excel(file_path, sheet_name='ship', header=0, index_col=None)
df_quay = pd.read_excel(file_path, sheet_name='quay', header=0, index_col=None)

# Collect ship names from the A column
ship_list = df_ship['Ship_Name'].unique().tolist()  # 'J-1', 'J-2', ...
work_list = df_ship['Operation_Type'].unique().tolist()  # '시운전', '축계작업' 등

quay_list = df_quay.columns.tolist()
quay_list = quay_list[2:]  # 1열, 2열의 header인 '선종'과 '작업'은 제외

# Initialize a dictionary to store operation lists for each ship
ship_operations = {}  # ship 별로 필요한 work의 리스트
ship_operation_duration = {}  # ship 작업별로 Duration 열의 값을 저장
quay_data = {}  # 안벽 이름을 저장할 예정
ship_quay = {}  # ship 별로 작업 가능한 안벽을 작업 순서대로 리스트로 저장

kor_to_eng = {}  # Operation Type 이름이 한글이라 깨지는 문제를 해결
for i, p in enumerate(work_list):
    kor_to_eng[p] = 'P' + str(i)

# Add a new column 'Operation_Eng' based on mapping
df_ship['Operation_Eng'] = df_ship['Operation_Type'].map(kor_to_eng)
df_quay['작업_Eng'] = df_quay['작업'].map(kor_to_eng)

work_list = df_ship['Operation_Eng'].unique().tolist()

# Iterate through each ship and collect corresponding operation names
for ship in ship_list:
    # Filter rows where 'A' column matches the current ship name
    ship_data = df_ship[df_ship['Ship_Name'] == ship]

    # Collect operation names from the I-th column
    operation_names = ship_data['Operation_Eng'].values.tolist()
    type_name = ship_data['Ship_Type'].values.tolist()
    ship_operation_duration[ship] = ship_data['Duration'].values.tolist()

    # Store operation names in the dictionary
    ship_operations[ship] = []
    for i in range(len(operation_names)):
        ship_operations[ship].append((type_name[i], operation_names[i]))

"""
ship_operations

key : job name
value : list of tuple(job type, work)

'J-1': [('S_COT', '축계작업'), ('S_COT', '시운전'), ('S_COT', '인도준비')], 
'J-2': [('S_COT', '축계작업'), ('S_COT', '시운전'), ('S_COT', '인도준비')], 
'J-3': [('S_SHTL', '축계작업'), ('S_SHTL', '시운전'), ('S_SHTL', '인도준비')]

"""

"""
ship_operation_duration

key : job name
value : list of integers

'J-1': [23, 63, 125]

"""

for index, row in df_quay.iterrows():
    shiptype = row['선종']
    worktype = row['작업_Eng']

    if (shiptype, worktype) not in quay_data:
        quay_data[(shiptype, worktype)] = {}
    for q in quay_list:
        priority = row[q]
        if priority != 'N':
            if priority not in quay_data[(shiptype, worktype)]:
                quay_data[(shiptype, worktype)][priority] = [q]
            else:
                quay_data[(shiptype, worktype)][priority].append(q)
"""
quay_data

key: tuple (shiptype, worktype)
value: machine list by priority 

(LNG, 화물창)
└─ A : A2, A3, A4, ...
└─ D : E1, E2, E3, ...

(LNG, P/T)
└─ A : A4, B2, B3, ...
└─ E : A1, A2, A3, ...

"""
for ship in ship_list:
    op_list = ship_operations[ship]
    ship_quay[ship] = []
    for op in op_list:
        ship_quay[ship].append(quay_data[op])

"""
ship_quay

key: ship name
value: dictionary value of quay_data by work

'J-1' : 
[ (LNG, 화물창) work data,  (LNG, P/T) work data, ... ] 

"""


class JobType:
    def __init__(self, jobtype, process_order, machine_order, processing_time):
        self.jobtype = jobtype

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


def generate_jobtype(idx):
    # jobname = ship_list[idx-1]
    jobname = 'J'+str(idx)
    processes = [ship_operations[jobname][i][1] for i in range(len(ship_operations[jobname]))]

    machines = ship_quay[jobname]
    best_machine = []
    for i in range(len(ship_operations[jobname])):
        if 'A' in machines[i]:
            m = machines[i]['A']
            best_machine.append(m)
        elif 'B' in machines[i]:
            m = machines[i]['B']
            best_machine.append(m)
        elif 'C' in machines[i]:
            m = machines[i]['C']
            best_machine.append(m)
        elif 'D' in machines[i]:
            m = machines[i]['D']
            best_machine.append(m)
        elif 'E' in machines[i]:
            m = machines[i]['E']
            best_machine.append(m)
        else:
            m = machines[i]['F']
            best_machine.append(m)
    pt = ship_operation_duration[jobname]

    job = JobType(jobname, processes, best_machine, pt)
    return job


job_list = [] # ship_list 정보에 따라 생성된 JobType 개체들의 리스트
for i in range(50):
    job = generate_jobtype(i + 1)
    job_list.append(job)

# print(job_list[0].jobtype)
# print(job_list[0].process_order)
# print(job_list[0].machine_order)
# print(job_list[0].processing_time)
