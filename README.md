## Capstone

## Prework

## Step 1

Create a node in CloudLab and git clone this repo to the node.
chmod 777 install.sh then run it. ( This is to install docker in the virtue machine)

## step 2

I have uploaded a docker image in fuzzychen/10batch, the start_container.py  will automatically start the container named test1 and record all the information we need.


## step 3:
There is no step 3


## Scripts Instruction

- install.sh (Install docker)
- main.py (algorithm1 script)
- alg2.py (algorithm2 script)
- alternate.py (alg1 & alg2)
- start_container_seven.py (start seven containers at the same time)
- competition.py (without any algorithm)
- start_container.py (start one container)
- random_add.py (start container randomly)

if you want to test algorithm1 or algorithm2 separately, please run 'start_container_seven.py' firstly;
start_container.py is the file just start one container, I run it before running 'random_add.py' when I test. But I already put all code in the 'random_add.py'. So you can run random_add.py directly. If there any questions, please check the script. 

If you have any questions, please let me know. Thanks!



Docker Swarm install
Step 1
install docker in all nodes.
chmod 777 install.sh
./install.sh

Step 2
In master node
init docker swarm by using:
docker swarm init

The output contains the: docker swarm join-token command 

Step 3
Copy swarm token command and paste in each workers, which let the worker join in the Swarm

check the state
-- docker node ls
-- docker service ls



update git`
git pull origin master


