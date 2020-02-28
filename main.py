import pandas as pd
import numpy as np
import re
import subprocess
import time
from os import popen
import random
import copy

cpus = 16

def get_container_list():
    command_name = ('docker stats --no-stream --format "table {{.Name}}"')
    container_name = subprocess.getoutput(command_name)
    container_list = container_name.splitlines()[1:]
    container_num = len(container_list)
    return container_list,container_num

container_list,container_num = get_container_list()

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
        final_data[temp_data[0]] = float(temp_data[1][:-1])/(cpus*100)
    return final_data


container_model_list = ["fuzzychen/1000batch","fuzzychen/vgg16","fuzzychen/inceptionv3","fuzzychen/res50","fuzzychen/xcep"]
def run_container(container_name,container_model):
    command_run = 'nohup docker run --name {} {} > {}.log &'.format(container_name,container_model,container_name)
    subprocess.Popen(command_run,shell=True)
    print("Succesfully run container ",container_name,"collecting data now!")

def number_regulate(x):
    if x > cpus:
        x = cpus
    elif x < 0.2:
        x = 0.2
    return round(x,2)

#Initialize
temp_cpu = get_cpu()
resource = [round(temp_cpu[i]*cpus,2) for i in container_list]
resource_history = []
print('The default Limit is: ',resource_history)
performance_history = []
performance_history1 = []
#target = [10+i for i in range(container_num)]
target = [20,20,20,20,20,20,20]
#for i in range(container_num):
#    target.append(random.randint(15,40))
print("The container list is: ",container_list)
print("The target time is: ",target)


alpha = 0.2


history_batch_time = {}
usage_history = get_cpu()
for i in usage_history:
    usage_history[i] = [usage_history[i]]

for t in range(25):
    # G = too fast,  D = too slow, B = balanced
    start_time = time.time()
    G,B,D  = [],[],[]
    Rg,Rd,Qg,Qd = 0,0,0,0
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
            adjust_list.append(i)

        current_performance = float(current_performance)
        performance.append(current_performance)
        q[i] = target[i] - current_performance

        if q[i] > target[i]*0.1:
            G.append(container_list[i])
            #Rg += resource[i]
            Qg += q[i]
        elif q[i] < -target[i]*0.1:
            D.append(container_list[i])
            #Rd += resource[i]
            Qd += q[i]
        else:
            B.append(container_list[i])

    #setting update rate depends onn how many container left to adjust
    print("The adjust adjust_rate_B is ",adjust_list)
    G_update_rate = len(G) * alpha
    D_update_rate = len(D) * alpha

    for i in adjust_list:
        if container_list[i] in G:
            resource[i] *= 1 - (q[i]/Qg)*G_update_rate
            resource[i] = number_regulate(resource[i])
        elif container_list[i] in D:
            resource[i] *= 1 + (q[i]/Qd)*D_update_rate
            resource[i] = number_regulate(resource[i])
        command_log = 'docker update --cpus {} {}'.format(resource[i],container_list[i])
        subprocess.Popen(command_log,shell=True)

    print("The G  at:",t,"Round still have",G)
    print("The D  at:",t,"Round still have",D)
    print("The Limit at:",t,'Round', resource)
    performance_history.append([len(G),len(D)])
    performance_history1.append([Qg,Qd])
    update_resource = copy.deepcopy(resource)
    resource_history.append(update_resource)
    print(resource_history)
    print("The balanced container: ",B)

    time.sleep(20)


performance_history = np.array(performance_history)
performance_record = pd.DataFrame({'G': performance_history[:,0], 'D': performance_history[:, 1]})
performance_history1 = np.array(performance_history1)
performance_record1 = pd.DataFrame({'G': performance_history1[:,0], 'D': performance_history1[:, 1]})
resource_history = np.array(resource_history)
resource_record = pd.DataFrame(resource_history,columns = container_list)
usg_record = pd.DataFrame.from_dict(usage_history)

usg_record.to_csv("u.csv")
performance_record.to_csv("p.csv")
performance_record1.to_csv("p1.csv")
resource_record.to_csv("r.csv")
