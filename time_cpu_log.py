import pandas as pd
import re
import subprocess
import time
from os import popen
# create a new dataframe
time_cpu_table = pd.DataFrame(columns = ['Container_id','Name','CPU','Batch_time','Batch_count'])

#CPU data ['container_id','container_name',CPU_percent,MEM_percent]
def get_cpu():
    command_cpu = ('docker stats --no-stream --format "table {{.Name}}\t{{.CPUPerc}}"')
    cpu_log = subprocess.getoutput(command_cpu)
    cpu_data =  cpu_log.splitlines()[1:]
    final_data = {}
    for i in cpu_data:
        temp_data = re.split('\s+', i)
        final_data[temp_data[0]] = temp_data[1:]
    return final_data

#since the log file is a string we need to split it and get start line number

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

def get_container_table(container_name):
    # create a new dataframe
    time_cpu_table = pd.DataFrame(columns = ['Container_name','CPU','Batch_time','Batch_count'])

    for i in range(50):
        try:
            cpu_data = get_cpu()
        except:
            print("There is no container running!!!!")
            break

        batch_time = get_batch_time(container_name)
        batch_count = len(batch_time)

        if len(batch_time) == 0:
            current_batch_time = 0
        else:
            temp_time = batch_time[-1]
            current_batch_time = float(temp_time[:6])

        current_cpu = cpu_data[container_name][0]
        current_cpu = float(current_cpu[:-1])

        batch_data = {'Container_name':container_name,'CPU':current_cpu,'Batch_time':current_batch_time,'Batch_count':batch_count}
        time_cpu_table = time_cpu_table.append(batch_data,ignore_index=True)

        print(time_cpu_table)
        time.sleep(3)

    learning_table = time_cpu_table[['CPU','Batch_time','Batch_count']]
    learning_table = learning_table.groupby(['Batch_count']).mean()
    print('--------------------:Here comes final table')
    print(learning_table)
    learning_table.to_csv("test1.csv")
    return learning_table

print(get_container_table("test1"))
