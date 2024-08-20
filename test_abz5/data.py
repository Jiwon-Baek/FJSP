import pandas as pd
# pandas 라이브러리 임포트. 데이터 조작과 분석 가능

"""
Please make sure the filepath is correct!
"""
data = pd.read_csv('./abz5.csv', header=None)
solution = pd.read_csv('./abz5_solution_start.csv', header=None)
# data, solution이라는 변수에 각 파일을 dataframe 형식으로 불러옴
# none header는 열이 없다는 뜻. 첫번째 행부터 데이터로 사용

abz5_process_list = ['P' + str(i + 1) for i in range(10)]
abz5_machine_list = ['M' + str(i + 1) for i in range(10)]
# 각 작업('P1'~'P10'), 머신('M1'~'M10') 리스트 생성

abz5_process = {}
abz5_duration = {}
abz5_machine = {}
# abz5에 대한 process, duration, machine 딕셔너리 생성.
for i in range(10):
    abz5_process['J' + str(i + 1)] = []
    abz5_duration['J' + str(i + 1)] = []
    abz5_machine['J' + str(i + 1)] = []
    # process, duration, machine에 대한 특정 작업(J1~J10)에 대한 정보 저장을 위한 초기화
    for j in range(10):
        abz5_process['J' + str(i + 1)].append('P' + str(data.iloc[10 + i, j]))
        abz5_duration['J' + str(i + 1)].append(data.iloc[i, j])
        abz5_machine['J' + str(i + 1)].append('M' + str(data.iloc[10 + i, j]))
        # data.iloc을 통해 공정 번호를 가지고 와, 각 작업의 공정순서, 지속시간, 할당 기계를 저장.
        # iloc: 위치기반 인덱싱[row, column] 0부터 시작, 행과 열을 나타냄.
solution_machine_order = [[] for i in range(10)]
for i in range(10):
# 10개의 기계 각각에 대해 반복 수행
    start_time = list(solution.iloc[:, i])
    # solution 데이터프레임에서 i번째 기계의 시작 시간을 추출
    value = sorted(start_time, reverse=False)
    # 시작 시간을 오름차순으로 정렬
    solution_machine_order[i] = sorted(range(len(start_time)), key=lambda k: start_time[k])
    # 시작 시간 리스트의 갯수별 시퀀스를 생성하고 해당 값을 정렬하도록 지시. 각 key에 대한 값을 매핑한 후
    # start_time의 요소가 오름차순으로 정렬될때의 원래 인덱스를 나타냄.
    # ex) start_time = [50, 30, 40, 45, 35] -> [1, 4, 2, 3, 0]
    # 기계 시작 시간을 기준으로 작업의 실행 순서를 결정.

# JobType 클래스를 정의합니다.
class JobType:
# jobtype 클래스 정의
    def __init__(self, jobtype, process_order, machine_order, processing_time):
        self.jobtype = jobtype
        # 작업 유형을 저장(예: 'J1', 'J2', ...).
        self.process_order = process_order
        # a list of 10 elements (e.g. ['Process5','Process4',...,'Process9']).
        # 작업 공정 순서 저장.
        self.machine_order = machine_order
        # a list of 10 elements, each element notes the set of compatible machines as tuple
        # 기계 집합을 튜플로 저장
        # (e.g. [('M1','M2'), ('M2','M3'), ... , ('M7','M8','M9')] )
        self.processing_time = processing_time
        # 각 공정 처리시간 저장
        self.num_process = len(process_order)
        # 공정의 수를 나타내는 변수.

        """
        When the JobType object is created, it will be delivered to Source constructor
        jobtype 객체 생성될 때, 이 객체는 Source 생성자에 전달.
        """


job_list = []  # abz5 정보에 따라 생성된 JobType 개체들의 리스트
for i in range(10):
    # 10개의 작업에 대한 반복 수행하며 JobType 객체 생성, job_list에 추가.
    job = JobType('J'+str(i+1),
                  abz5_process['J' + str(i + 1)],
                  abz5_machine['J' + str(i + 1)],
                  abz5_duration['J' + str(i + 1)])
    # job은 jobtype 클래스에 각 job과 해당 job에 대한 process, machine, duration을 나타내는 JobType 클래스의 인스턴스.
    job_list.append(job)



