import pandas as pd

"""
Please make sure the filepath is correct!
"""
data = pd.read_csv('./abz5.csv', header=None)
solution = pd.read_csv('./abz5_solution_start.csv', header=None)

abz5_process_list = ['P' + str(i + 1) for i in range(10)]
abz5_machine_list = ['M' + str(i + 1) for i in range(10)]
abz5_process = {}
abz5_duration = {}
abz5_machine = {}
for i in range(10):
    abz5_process['J' + str(i + 1)] = []
    abz5_duration['J' + str(i + 1)] = []
    abz5_machine['J' + str(i + 1)] = []
    for j in range(10):
        abz5_process['J' + str(i + 1)].append('P' + str(data.iloc[10 + i, j]))
        abz5_duration['J' + str(i + 1)].append(data.iloc[i, j])
        abz5_machine['J' + str(i + 1)].append('M' + str(data.iloc[10 + i, j]))

solution_machine_order = [[] for i in range(10)]
for i in range(10):
    start_time = list(solution.iloc[:, i])
    value = sorted(start_time, reverse=False)
    solution_machine_order[i] = sorted(range(len(start_time)), key=lambda k: start_time[k])


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


job_list = []  # abz5 정보에 따라 생성된 JobType 개체들의 리스트
for i in range(10):
    job = JobType('J'+str(i+1),
                  abz5_process['J' + str(i + 1)],
                  abz5_machine['J' + str(i + 1)],
                  abz5_duration['J' + str(i + 1)])
    job_list.append(job)


