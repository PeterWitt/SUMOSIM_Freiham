from ast import Delete
import traci
import numpy
from datetime import datetime
import tools
import argparse

parser = argparse.ArgumentParser()

parser.add_argument("--gui", action="store_true", help='Open SUMO with GUI')
parser.add_argument("-c", "--config", type=str, required=True, help='Set SUMO configuration file')
parser.add_argument("--numVeh", type=int, required=True, nargs=2, help='Number of vehicles to be recorded. Enter the total number and the number of vehicles from Pasing. Separate with comma. Example: 450, 5 (450 vehicles in total, 5 vehicles are used at each berth in Pasing)')
parser.add_argument("--freqRebalance", type=int, default=5, help='Rebalance frequency. Value is every x seconds')
parser.add_argument("--freqRebalanceStation", type=int, default=10, help='Rebalancing to Pasing frequency. Value is every x seconds')
parser.add_argument("--dispatchAlgorithm", type=str, required=True, help='Name of SUMO dispatch algorithm')
parser.add_argument("--dispatchParam", type=str, default = 'absLossThreshold', help='Set Trashold kind. If dispatch algorithm is greedyShared')
parser.add_argument("--dispatchThreshold", type=int, default = 0, help='Value of Trashold if dispatch algorithm is greedyShared')
parser.add_argument("--outputPrefix", type=str, default="False", help='Prefix of outpuftfiles')
parser.add_argument("-v", "--verbos", action="store_true")

args = parser.parse_args()

shared = False

if args.gui:
    sumoBinary = "C:\Program Files (x86)\Eclipse\Sumo\\bin\sumo-gui.exe"
else:
    sumoBinary = "C:\Program Files (x86)\Eclipse\Sumo\\bin\sumo.exe"

if args.dispatchAlgorithm == "greedyShared":
    dispatch_algo = f"--device.taxi.dispatch-algorithm=greedyClosest"
    dispatch_params = f"--device.taxi.dispatch-algorithm.params={args.dispatchParam}:{args.dispatchThreshold}"
    shared = True
else:
    dispatch_algo = f"--device.taxi.dispatch-algorithm={args.dispatchAlgorithm}"

if args.outputPrefix == "False":
    output_prefix = str(args.numVeh[0]) + args.dispatchAlgorithm
    if shared:
        output_prefix = output_prefix+ args.dispatchParam + str(args.dispatchThreshold)
else:
    output_prefix = args.outputPrefix

num_veh_freiham = args.numVeh[0] - 2*args.numVeh[1]
num_veh_pasing = args.numVeh[1]

if not shared:
    sumoCmd = [sumoBinary, "-c", args.config, dispatch_algo, "--start", "true", "--ignore-route-errors", "--device.taxi.idle-algorithm=randomCircling",
        "--collision.action=none", "--extrapolate-departpos=true", "--output-prefix="+output_prefix+"_"]
else:
    sumoCmd = [sumoBinary, "-c", args.config, dispatch_algo, dispatch_params, "--start", "true", "--ignore-route-errors", "--device.taxi.idle-algorithm=randomCircling",
        "--collision.action=none", "--extrapolate-departpos=true", "--output-prefix="+output_prefix+"_"]


print(sumoCmd)

step = 0

traci.start(sumoCmd)

while step < 100000:
    traci.simulationStep()

    if args.verbos and step % 1000 == 0:
        print(f"Step = {step}")

    tools.rebalance_basic(step, 5, 10)

    if step == 0:
        tools.create_fleet(f"{num_veh_freiham}:depot_main1,{num_veh_pasing}:depot_pasing1,{num_veh_pasing}:depot_pasing2")

    if step < 25200 and step % 60 == 0:
        tools.rebalance_low_demand(1)

    if 79200 < step < 86400 and step % 60 == 0:
        tools.rebalance_low_demand(1)     
 
    step += 1

traci.close()