import os

# [--gui, config, numVeh Freiham, numVeh Pasing, freqRebalance, freqRebalanceStation, dispatchAlgorithm, dispatchParam, dispatchThreshold, outputPrefix, -v]

sim1 = [False, "freiham.sumocfg", "450", "5", False, False, "greedyShared", "absLossThreshold", "60", False, "-v"]
sim2 = [False, "freiham.sumocfg", "450", "5", False, False, "greedyShared", "absLossThreshold", "120", False, "-v"]
sim3 = [False, "freiham.sumocfg", "450", "5", False, False, "greedyShared", "absLossThreshold", "240", False, "-v"]
sim4 = [True, "freiham.sumocfg", "300", "5", False, False, "greedyClosest", False, False, False, "-v"]

arg_list=[sim1, sim2, sim3, sim4]

for args in arg_list:
    config = ""
    if args[0]:
        config = config + " --gui"
    config = config + " -c " + args[1]
    config = config + " --numVeh " + args[2] + " " + args[3]
    if args[4]:
        config = config + " --freqRebalance " + args[4]
    if args[5]:
        config = config + " --freqRebalanceStation " + args[5]
    config = config + " --dispatchAlgorithm " + args[6]
    if args[7]:
        config = config + " --dispatchParam " + args[7]
    if args[8]:
        config = config + " --dispatchThreshold " + args[8]
    if args[9]:
        config = config + " --outputPrefix " + args[9]
    if args[10]:
        config = config + " -v "

    print("Current simulation config: " + config)
    try:
        os.system("sumo_start.py" + config)
    except:
        print("Simulation with config: " + config + " FAILED")
    else:
        print("Simulation with config: " + config + " SUCCESS!")
