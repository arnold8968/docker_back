import pandas as pd
import numpy as np
import re
import subprocess
import time
from os import popen
import random
import copy
import matplotlib.pyplot as plt 

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
        final_data[temp_data[0]] = temp_data[1:]
    return final_data

#Initialize
resource = [20] * container_num
resource_history = []
print('The default Limit is: ',resource_history)
performance_history = []
performance_history1 = []
target = [10,10,10,10,10,10,10]
#for i in range(container_num):
#    target.append(random.randint(15,40))
print("The container list is: ",container_list)
print("The target time is: ",target)


alpha = 0.2


#more_container = ["test6","test7","test8","test9"]
add = 0

history_batch_time = {}

for t in range(30):
    # G = too fast,  D = too slow, B = balanced
    start_time = time.time()
    G,B,D  = [],[],[]
    Rg,Rd,Qg,Qd = 0,0,0,0
    performance = []
    q = [0] * container_num
    adjust_list = []
    for i in range(container_num):
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

        if q[i] > target[i]*0.1:
            G.append(container_list[i])
            #Rg += resource[i]
            Qg += q[i]
        elif q[i] < -(target[i]*0.1):
            D.append(container_list[i])
            #Rd += resource[i]
            Qd += q[i]
        else:
            B.append(container_list[i])

    #setting update rate depends onn how many container left to adjust
    update_rate = (container_num - len(B)) * alpha


    for i in adjust_list:
        # q[i] > 3
        if container_list[i] in G:
            resource[i] = resource[i] * ( 1 - (q[i]/Qg)*update_rate)
            print('the value is:',resource[i])
            if resource[i] > 20:
                resource[i] = 20
        
            resource[i] = round(resource[i],1)
        # q[i] < -3
        elif container_list[i] in D:
            resource[i] *= 1 + (q[i]/Qd)*update_rate
            if resource[i] < 0.2:
                resource[i] = 0.2
            resource[i] = round(resource[i],1)

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
    '''
    if t in [2,5,10,15]:
        #add more containers
        run_container(more_container[add],container_model_list[add])
        add += 1
        container_list,container_num = get_container_list()
        resource.append(16)
        target.append(random.randint(15,40))
    '''

    time.sleep(35)


performance_history = np.array(performance_history)
performance_record = pd.DataFrame({'G': performance_history[:,0], 'D': performance_history[:, 1]})
performance_history1 = np.array(performance_history1)
performance_record1 = pd.DataFrame({'G': performance_history1[:,0], 'D': performance_history1[:, 1]})
resource_history = np.array(resource_history)
resource_record = pd.DataFrame(resource_history,columns = container_list)

performance_record.to_csv("same_target_p.csv")
performance_record1.to_csv("same_target_p1.csv")
resource_record.to_csv("same_target_cpu.csv")

plt.figure(0)
plt.plot(performance_record["G"])
plt.plot(performance_record["D"])
plt.ylabel('Unbalanced Containers')
plt.xlabel('Round')
plt.legend(('Qg','Qd'),loc='upper right')
plt.grid()
plt.savefig('same_target_p.png')

plt.figure(1)
plt.plot(performance_record1["G"])
plt.plot(performance_record1["D"])
plt.ylabel('Unbalanced Performance')
plt.xlabel('Round')
plt.legend(('Qg','Qd'),loc='upper right')
plt.grid()
plt.savefig('same_target_p1.png')


plt.figure(2)
plt.plot(resource_record,column = container_list)
plt.ylim(0, 4)
plt.ylabel('Resource Allocation')
plt.xlabel('Round')
plt.legend(container_list,loc='upper right')
plt.grid()
plt.savefig('same_target_cpu.png')
