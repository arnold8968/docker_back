import pandas as pd
import numpy as np
import re
import subprocess
import time
from os import popen
import random
import copy


def get_container_list():
    command_name = ('docker stats --no-stream --format "table {{.Name}}"')
    container_name = subprocess.getoutput(command_name)
    container_list = container_name.splitlines()[1:]
    container_num = len(container_list)
    return container_list, container_num


container_list, container_num = get_container_list()
cpus = 16


def get_container_startline(container_name):
    command_log = 'docker logs {}'.format(container_name)
    time_log = subprocess.getoutput(command_log)
    batch_log = time_log.splitlines()
    start_count = 0
    for i in batch_log:
        if "0us/step" in i:
            break
        start_count += 1
    return start_count


def get_batch_time(container_name):
    command_log = 'docker logs {}'.format(container_name)
    time_log = subprocess.getoutput(command_log)
    batch_time = time_log.splitlines()
    start_line = get_container_startline(container_name)
    batch_time = batch_time[start_line + 1:]
    return batch_time


# Get cpu_percentage
def get_cpu():
    command_cpu = ('docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}"')
    cpu_log = subprocess.getoutput(command_cpu)
    cpu_data = cpu_log.splitlines()[1:]
    final_data = {}
    for i in cpu_data:
        temp_data = re.split('\s+', i)
        final_data[temp_data[0]] = float(temp_data[1][:-1]) / (cpus * 100)
    return final_data


def run_container(container_name, container_model):
    command_run = 'nohup docker run --name {} {} > {}.log &'.format(container_name, container_model, container_name)
    subprocess.Popen(command_run, shell=True)
    print("Succesfully run container ", container_name, "collecting data now!")


def number_regulate(x):
    if x > cpus:
        x = cpus
    elif x < 0.2:
        x = 0.2
    return round(x, 2)


# Initialize

temp_cpu = get_cpu()
resource = [round(temp_cpu[i] * cpus, 2) for i in container_list]

resource_history, performance_history, performance_history1 = [], [], []
print('The default Limit is: ', resource)
# target = [10+i for i in range(container_num)]
target = [20, 20, 20, 20, 20, 20, 20]
print("The container list is: ", container_list)
print("The target time is: ", target)

history_batch_time = {}
usage_history = get_cpu()
for i in usage_history:
    usage_history[i] = [usage_history[i]]

E_state = np.ones((2, 3))

for t in range(30):
    # G = too fast,  B = bad----too slow , S = stay the  same ( balanced)
    G, B, S = [], [], []
    Rg, Rb, Qg, Qb = 0, 0, 0, 0
    performance = []
    q = [0] * container_num
    adjust_list = []

    for i in range(container_num):
        cpu_data = get_cpu()
        current_cpu = cpu_data[container_list[i]]
        usage_history[container_list[i]].append(current_cpu)

        current_performance = get_batch_time(container_list[i])[-1]
        if container_list[i] in history_batch_time:
            if current_performance != history_batch_time[container_list[i]]:
                history_batch_time[container_list[i]] = current_performance
                adjust_list.append(i)
        else:
            history_batch_time[container_list[i]] = current_performance

        current_performance = float(current_performance)
        performance.append(current_performance)
        q[i] = target[i] - current_performance

        if q[i] > target[i] * 0.1:
            G.append(container_list[i])
            # cpus = 20
            Rg += current_cpu
            Qg += q[i]
        elif q[i] < -target[i] * 0.1:
            B.append(container_list[i])
            Rb += current_cpu
            Qb += q[i]
        else:
            S.append(container_list[i])

    E_state[1, 0] = Qg + abs(Qb)
    E_state[1, 1] = Qg / E_state[1, 0]
    E_state[1, 2] = abs(Qb) / E_state[1, 0]
    alpha = abs((E_state[1, 1] - E_state[1, 2]) / 2)

    print('The E_state[1,1] is:', E_state[1, 1])
    print('The E_state[0,1] is:', E_state[0, 1])

    # alpha = 0.2
    # 10% of variance
    if E_state[0, 0] != 0 and E_state[1, 0] > E_state[0, 0]:
        if E_state[0, 1] != 0 and E_state[1, 1] > E_state[0, 1]:
            adjust_rate_G = 1 - alpha
            print('adjust_rate_G_ :', adjust_rate_G)
            adjust_rate_B = (Rb + Rg * alpha) / Rb
            print('adjust_rate_B_ :', adjust_rate_B)
            Rb = Rb + Rg * alpha
            Rg *= 1 - alpha
        elif E_state[0, 1] != 0 and E_state[1, 1] >= E_state[0, 1]:
            adjust_rate_G = 1 - alpha / 2
            print('adjust_rate_G_ :', adjust_rate_G)
            adjust_rate_B = (Rb + Rg * alpha / 2) / Rb
            print('adjust_rate_B_ :', adjust_rate_B)
            Rb = Rb + Rg * alpha / 2
            Rg *= 1 - alpha / 2

    E_state[0] = E_state[1]
    print('The adjust_rate_B is ', adjust_rate_B)
    print('The adjust_rate_G is ', adjust_rate_G)
    print('The adjust list is ', adjust_list)
    for i in adjust_list:
        if container_list[i] in G:
            resource[i] *= (1 - q[i] / Qg * adjust_rate_G)
            resource[i] = number_regulate(resource[i])

        elif container_list[i] in B:
            resource[i] *= (1 + q[i] / Qb * adjust_rate_B)
            resource[i] = number_regulate(resource[i])

        command_log = 'docker update --cpus {} {}'.format(resource[i], container_list[i])
        subprocess.Popen(command_log, shell=True)

    print("The G  at:", t, "Round still have", G)
    print("The B  at:", t, "Round still have", B)
    print("The Limit at:", t, 'Round', resource)
    performance_history.append([len(G), len(B)])
    performance_history1.append([Qg, Qb])
    update_resource = copy.deepcopy(resource)
    resource_history.append(update_resource)
    print("The balanced container: ", S)

    '''
    if t in [2,5,10,15]:
        #add more containers
        run_container(more_container[add],container_model_list[add])
        add += 1
        container_list,container_num = get_container_list()
        resource.append(16)
        target.append(random.randint(15,40))

    time.sleep(20)
    '''

performance_history = np.array(performance_history)
performance_record = pd.DataFrame({'G': performance_history[:, 0], 'D': performance_history[:, 1]})
performance_history1 = np.array(performance_history1)
performance_record1 = pd.DataFrame({'G': performance_history1[:, 0], 'D': performance_history1[:, 1]})
resource_history = np.array(resource_history)
resource_record = pd.DataFrame(resource_history, columns=container_list)
usg_record = pd.DataFrame.from_dict(usage_history)

usg_record.to_csv("u.csv")
performance_record.to_csv("p.csv")
performance_record1.to_csv("p1.csv")
resource_record.to_csv("r.csv")