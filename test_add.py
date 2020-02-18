import pandas as pd
import numpy as np
import re
import subprocess
import time
import random

#clear all history
command_stop = "docker kill $(sudo docker ps -q)"
subprocess.Popen(command_stop, shell=True)
time.sleep(10)
command_clear = "docker rm $(sudo docker ps -a -q)"
subprocess.Popen(command_clear, shell=True)
time.sleep(10)

# Initialize
container_model_list = ["fuzzychen/1000batch","fuzzychen/vgg16","fuzzychen/inceptionv3","fuzzychen/Xception","fuzzychen/ResNet50"]
#model = random.choice(container_model_list)
start_container_list = ["test1","test2","test3","test4","test5"]

# start_container
def run_container(container_name,container_model):
    command_run = 'nohup docker run --name {} {} > {}.log &'.format(container_name,container_model,container_name)
    subprocess.Popen(command_run, shell=True)
    print("Succesfully run container ", container_name, "collecting data now!")
    
for i in range(5):
    model = random.choice(container_model_list)
    print(model)
    run_container(start_container_list[i], model)
print('initializing -------- Takes 10 seconds')
time.sleep(120)

