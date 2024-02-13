# region Operation
class Operation(object):
    """
    This class does not act as a process.
    Instead, this is just a member variable of a job that contains process info.
    This class is only used when generating a job sequence.
    The Process class is to be generated further.
    """

    def __init__(self, model, env, id, part_name, process_type, machine_list, process_time, requirements=None):
        self.model = model
        self.id = id  # Integer
        self.process = self.model[process_type]  # Convert String to Process Object
        self.process_time = process_time  # Integer, or given as List
        self.part_name = part_name  # Inherited
        self.name = part_name + '_Op' + str(id)

        # In the simplest Job Shop problem, process type is often coincide with the machine type itself.
        self.machine_list = machine_list  # list of strings
        self.machine_available = [self.model[machine_list[i]] for i in range(len(machine_list))]

        self.machine_determined = None
        self.machine_determined_idx = None
        self.process_time_determined = None

        if requirements is None:
            self.requirements = env.event()  # preceding event
            if id == 0:
                self.requirements.succeed()
        else:
            # if there are more requirements, more env.event() can be added up
            # you can handle events using Simpy.AllOf() or Simpy.AnyOf()
            self.requirements = [env.event() for i in range(5)]  # This is an arbitrary value


# endregion

# region Job
class Job(object):
    """
    A job is to be repeatedly generated in a source.
    (Job1_1, Job1_2, Job1_3, ..., Job1_100,
    Job2_1, Job2_2, Job2_3, ..., Job2_100,
    ...                         Job10_100)

    Member Variable : job_type, id
    """

    def __init__(self, model, env, job_type, id):
        self.model = model
        self.job_type = job_type
        self.num_process = job_type.num_process
        self.id = id
        # job_type.jobtype = 'J-1'
        # self.name = 'Part' + job_type.jobtype.split('-')[1] + '_' + str(id)
        self.name = job_type.jobtype + '_' + str(id)
        self.step = -1
        self.loc = None  # current location
        self.op = []
        self.env = env

        self.generate_operation()

    def generate_operation(self):
        for j in range(self.job_type.num_process):
            o = Operation(self.model, self.env,
                          id=j, part_name=self.name,
                          process_type=self.job_type.process_order[j],
                          machine_list=self.job_type.machine_order[j],
                          process_time=self.job_type.processing_time[j],
                          requirements=None)
            self.op.append(o)

# endregion Job
