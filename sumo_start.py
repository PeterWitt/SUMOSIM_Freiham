from ast import Delete
import traci
import numpy
from datetime import datetime
import tools 

sumoBinary = "C:\Program Files (x86)\Eclipse\Sumo\\bin\sumo-gui.exe"
sumoCmd = [sumoBinary, "-c", "freiham.sumocfg", "--device.taxi.dispatch-algorithm=greedyClosest", "--device.taxi.dispatch-algorithm.params=absLossThreshold:240", "--start", "true" , "--ignore-route-errors", "--device.taxi.idle-algorithm=randomCircling",
    "--collision.action=none", "--extrapolate-departpos=true"]
step = 0

traci.start(sumoCmd)

while step < 100000:
    traci.simulationStep()
    
    tools.rebalance_basic(step, 5, 10)
    
    if step == 0:
        tools.create_fleet("440:depot_main1,5:depot_pasing1,5:depot_pasing2")

    if step < 25200 and step % 60 == 0:
        tools.rebalance_low_demand(1)

    if step < 86400 and step > 79200 and step % 60 == 0:
        tools.rebalance_low_demand(1)     
 
    step += 1

traci.close()