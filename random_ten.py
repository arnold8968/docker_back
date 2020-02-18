import re
import subprocess
import time
from os import popen
import random
import pandas as pd
import numpy as np
import copy

cpu = 16
alpha = 0.2

# clear all history
command_stop = "docker kill $(sudo docker ps -q)"
subprocess.Popen(command_stop, shell=True)
time.sleep(10)
command_clear = "docker rm $(sudo docker ps -a -q)"
subprocess.Popen(command_clear, shell=True)
time.sleep(10)

# Initialize
container_model_list = ["fuzzychen/1000batch", "fuzzychen/vgg16", "fuzzychen/inceptionv3", "fuzzychen/Xception",
                        "fuzzychen/ResNet50"]
container_name_list = ["test1", 'test2', 'test3', 'test4', 'test5', 'test6', 'test7', 'test8', 'test9', 'test10']

# start_container
def run_container(container_name, container_model):
    command_run = 'nohup docker run --name {} {} > {}.log &'.format(container_name, container_model, container_name)
    subprocess.Popen(command_run, shell=True)
    print("Succesfully run container ", container_name, "collecting data now!")

def get_container_list():
    command_name = ('docker stats --no-stream --format "table {{.Name}}"')
    container_name = subprocess.getoutput(command_name)
    container_list = container_name.splitlines()[1:]
    container_num = len(container_list)
    return container_list, container_num

#container_list, container_num = get_container_list()

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
    batch_time = batch_time[start_line+1:]
    return batch_time

def get_cpu():
    command_cpu = ('docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}"')
    cpu_log = subprocess.getoutput(command_cpu)
    cpu_data =  cpu_log.splitlines()[1:]
    final_data = {}
    for i in cpu_data:
        temp_data = re.split('\s+', i)
        final_data[temp_data[0]] = float(temp_data[1][:-1])/(cpu*100)
    return final_data

def random_container():
    for i in range(10):
        model = random.choice(container_model_list)
        print(model)
        run_container(start_container_list[i], model)
    print('initializing -------- Takes 60 seconds')
    time.sleep(60)

# initialize
temp_cpu = get_cpu()
resource_history, performance_history, performance_history1 = [], [], []
history_batch_time = {}
usage_history = get_cpu()
for i in usage_history:
    usage_history[i] = [usage_history[i]]

for t in range(20):
    Rg, Rb, Qg, Qb = 0, 0, 0, 0
    performance = []
    q = [0]
    
    target = [20]
    for k in range(10):
        model = random.choice(container_model_list)
        print(model)
        run_container(container_name_list[k], model)
        print('initializing -------- Takes 60 seconds')
        time.sleep(55)

        container_list, container_num = get_container_list()
        resource = [round(temp_cpu[i] * cpu, 2) for i in container_list]
        print('The default Limit is: ', resource)
        target.append(20)
        print('The target time is:', target)
        q.append(0)
        
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

    #print("The resource are:", t, 'Round', resource)
   # performance_history.append([len(G), len(B)])
    performance_history1.append([Qg, Qb])
    update_resource = copy.deepcopy(resource)
    resource_history.append(update_resource)
    #print("The balanced container: ", S)

    time.sleep(10)

performance_history = np.array(performance_history)
#performance_record = pd.DataFrame({'G': performance_history[:, 0], 'D': performance_history[:, 1]})
performance_history1 = np.array(performance_history1)
#performance_record1 = pd.DataFrame({'G': performance_history1[:, 0], 'D': performance_history1[:, 1]})
resource_history = np.array(resource_history)
resource_record = pd.DataFrame(resource_history, columns=container_list)
usg_record = pd.DataFrame.from_dict(usage_history)

usg_record.to_csv("u_free.csv")
#performance_record.to_csv("p_free.csv")
performance_history1.to_csv("p1_free.csv")
resource_record.to_csv("r_free.csv")
