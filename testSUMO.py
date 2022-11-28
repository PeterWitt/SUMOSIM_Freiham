from ast import Delete
import traci
import numpy
from datetime import datetime


shuttle_rebalanced = {"pasing1": [], "pasing2": [], "freiham1": []}
prt_shuttle = []
shuttle_free_main_park = []

def createShuttle(route, num):
    #rou_num = numpy.random.randint(1, 12)
    traci.vehicle.add(f'taxiV{num}', route, typeID='shuttle', depart='now', departPos='free', departSpeed="avg", line='taxi')
    match route:
        case "depot_main1":
            traci.vehicle.setParkingAreaStop(f'taxiV{num}', "main_park1", duration=999999, flags=1)            
        case "depot_pasing1":
            traci.vehicle.setParkingAreaStop(f'taxiV{num}', "pasing_park1", duration=999999, flags=1)
            shuttle_rebalanced["pasing1"].append(f'taxiV{num}')
        case "depot_pasing2":
            traci.vehicle.setParkingAreaStop(f'taxiV{num}', "pasing_park2", duration=999999, flags=1)
            shuttle_rebalanced["pasing2"].append(f'taxiV{num}')


    return f'taxiV{num}'

def rebalancing_main():
    global prt_shuttle
    global shuttle_rebalanced
    global shuttle_free_main_park

    shuttle_free_main_park = []
    shuttle_to_be_rebalanced = []
    shuttle_parked_sidedepot = []

    shuttle_parked_sidedepot.extend(traci.parkingarea.getVehicleIDs("pasing_park1"))
    shuttle_parked_sidedepot.extend(traci.parkingarea.getVehicleIDs("pasing_park2"))

    free_shuttle = traci.vehicle.getTaxiFleet(0)
    main_park1_shuttle = traci.parkingarea.getVehicleIDs("main_park1")

    shuttle_parked = main_park1_shuttle + traci.parkingarea.getVehicleIDs("pasing_park1") + traci.parkingarea.getVehicleIDs("pasing_park2")
    shuttle_free_not_rebalanced = [shuttle for shuttle in free_shuttle if shuttle not in shuttle_rebalanced["pasing1"] and shuttle not in shuttle_rebalanced["pasing2"] and shuttle not in shuttle_rebalanced["freiham1"]]

    shuttle_to_be_rebalanced = [shuttle for shuttle in prt_shuttle if shuttle not in shuttle_parked and shuttle in shuttle_free_not_rebalanced]

    if 1 == 0:
        print("")
    
    for shuttle_name in shuttle_to_be_rebalanced:
        if not traci.vehicle.isStoppedParking(shuttle_name): 
            shuttle_edge = traci.lane.getEdgeID(traci.vehicle.getLaneID(shuttle_name) if traci.vehicle.getLaneID(shuttle_name) != '' else "258215507_0")
            try:
                if shuttle_edge in ["E21", "dropoff_lane2"]:
                    traci.vehicle.changeTarget(shuttle_name, traci.lane.getEdgeID(traci.parkingarea.getLaneID("pasing_park2")))
                    traci.vehicle.setParkingAreaStop(shuttle_name, "pasing_park2", duration=999999, flags=1)
                    shuttle_rebalanced["pasing2"].append(shuttle_name)
                elif shuttle_edge in ["E22", "dropoff_lane1"]:
                    traci.vehicle.changeTarget(shuttle_name, traci.lane.getEdgeID(traci.parkingarea.getLaneID("pasing_park1")))
                    traci.vehicle.setParkingAreaStop(shuttle_name, "pasing_park1", duration=999999, flags=1)
                    shuttle_rebalanced["pasing1"].append(shuttle_name)
                else: 
                    traci.vehicle.changeTarget(shuttle_name, traci.lane.getEdgeID(traci.parkingarea.getLaneID(f"main_park1")))
                    traci.vehicle.setParkingAreaStop(shuttle_name, "main_park1", duration=999999, flags=1)
            except traci.exceptions.TraCIException as e:
                print(e)
                continue    
            
    shuttle_free_main_park = [shuttle for shuttle in main_park1_shuttle if shuttle in shuttle_free_not_rebalanced]    

def rebalancing_helper():
    global prt_shuttle
    global shuttle_rebalanced
    global shuttle_free_main_park

    for park in ["pasing1", "pasing2", "freiham1"]:
        for shuttle in shuttle_rebalanced[park]:
            if traci.vehicle.isStoppedParking(shuttle) or traci.vehicle.getParameter(shuttle, "device.taxi.state") != "0":
                shuttle_rebalanced[park].remove(shuttle)
    
    num_vehicle_pasing1 = traci.parkingarea.getVehicleCount("pasing_park1")
    num_vehicle_pasing2 = traci.parkingarea.getVehicleCount("pasing_park2")
    empty_parkingspace_pasing1 = 5 - (num_vehicle_pasing1 + len(shuttle_rebalanced["pasing1"]))
    empty_parkingspace_pasing2 = 5 - (num_vehicle_pasing2 + len(shuttle_rebalanced["pasing2"]))
    
    if empty_parkingspace_pasing1 > 0:
        for i in range (0, empty_parkingspace_pasing1):
            if i >= 0 and i < len(shuttle_free_main_park):
                    traci.vehicle.resume(shuttle_free_main_park[i])
                    traci.vehicle.changeTarget(shuttle_free_main_park[i], traci.lane.getEdgeID(traci.parkingarea.getLaneID("pasing_park1")))
                    traci.vehicle.setParkingAreaStop(shuttle_free_main_park[i], "pasing_park1", duration=999999, flags=1)
                    shuttle_rebalanced["pasing1"].append(shuttle_free_main_park[i])
                    shuttle_free_main_park.remove(shuttle_free_main_park[i])
            else:
                break

    if empty_parkingspace_pasing2 > 0:            
        for i in range (empty_parkingspace_pasing1+1, empty_parkingspace_pasing1+1+empty_parkingspace_pasing2):
            if i >= 0 and i < len(shuttle_free_main_park):
                    traci.vehicle.resume(shuttle_free_main_park[i])
                    traci.vehicle.changeTarget(shuttle_free_main_park[i], traci.lane.getEdgeID(traci.parkingarea.getLaneID("pasing_park2")))
                    traci.vehicle.setParkingAreaStop(shuttle_free_main_park[i], "pasing_park2",  duration=999999, flags=1)
                    shuttle_rebalanced["pasing2"].append(shuttle_free_main_park[i])
                    shuttle_free_main_park.remove(shuttle_free_main_park[i])
            else:
                break


def rebalance_morning(anz):
    global prt_shuttle
    global shuttle_free_main_park
    global shuttle_rebalanced

    for shuttle in shuttle_rebalanced["freiham1"]:
        if traci.vehicle.getLaneID(shuttle) not in ["depot_main1_0", "depot_main1_1"] :
            if traci.vehicle.getParameter(shuttle, "device.taxi.state") == "0":
                traci.vehicle.setParkingAreaStop(shuttle, "main_park1", duration=999999, flags=1)
            else:
                shuttle_rebalanced["freiham1"].remove(shuttle)
            
    for i in range(0,anz):
        if i < len(shuttle_free_main_park):
            traci.vehicle.resume(shuttle_free_main_park[i])
            try:
                #traci.vehicle.setStopParameter(shuttle_free_main_park[i], 0, duration=0, flags=1)
                #traci.vehicle.changeTarget(shuttle_free_main_park[i], "-E50")
                #traci.vehicle.setVia(shuttle_free_main_park[i], ["-E44"])
                #traci.vehicle.setVia(shuttle_free_main_park[i], ["-464738721"])
                traci.vehicle.setRouteID(shuttle_free_main_park[i],"toggle_freiham1")
                #traci.vehicle.setParkingAreaStop(shuttle_free_main_park[i], "main_park1", duration=999999, flags=1)
                shuttle_rebalanced["freiham1"].append(shuttle_free_main_park[i])
                #print(shuttle_free_main_park[i])

            except:
                shuttle_free_main_park.remove(shuttle_free_main_park[i])



originList = ["-E65", "-E46", "E42", "-E55", "E57", "E40", "-E39.532", "-E69", "721302669#2", "-407581698#2", "407568055#4", "504565992#2"]
freihamLiving = ["-E65", "E65", "-E45", "E45", "-E46", "E46", "-E47", "E47", "-E44", "E44", "-E43", "E43", "-E48", "E48", "-E49", "E49", "-E51", "E51", "-E52", "E52", "-E69", "E69", "-E70", "E70", "-E71", "E71", "E72", "-E72", "E73", "-E73", "-E74", "E74", "504569022", "-504569022"]
destList = ["E39", "-721302669#2", "-513657853#0", "E31"]


def start_sumo_background_task():
    global prt_shuttle 
    
    sumoBinary = "C:\Program Files (x86)\Eclipse\Sumo\\bin\sumo-gui.exe"
    sumoCmd = [sumoBinary, "-c", "freiham.sumocfg", "--device.taxi.dispatch-algorithm=greedyShared", "--device.taxi.dispatch-algorithm.params=absLossThreshold:240", "--start", "true" , "--ignore-route-errors", "--device.taxi.idle-algorithm=randomCircling",
        "--collision.action=none", "--extrapolate-departpos=true"]

    traci.start(sumoCmd)
    step = 0
    count = 1
    managed_cust = []

    prt_shuttle = []
    while step < 100000:
                
        if (step+1)%1000 == 0:
            sim_start = datetime.now()
        
        traci.simulationStep()
        
     
        
        if (step+1)%1000 == 0:
           start = datetime.now()

        if step == 65937:
            print("")

        if step%5 == 0:
            start = datetime.now()
            rebalancing_main()
            stop = datetime.now()
            if step%1000 == 0:
                td = (stop - start).total_seconds() * 10**3
                print(f"The time of execution rebalancing at step {step} : {td:.03f}ms")
        if step%10 == 0:
            start = datetime.now()
            rebalancing_helper()
            stop = datetime.now()
            if step%1000 == 0:
                td = (stop - start).total_seconds() * 10**3
                print(f"The time of execution rebalancing helper at step {step} : {td:.03f}ms")

        if step < 600 and step % 30 == 0:
            rebalance_morning(2)
        elif step < 720 and step % 60 == 0:
            rebalance_morning(2)
        elif step < 14000 and step % 120 == 0:
            rebalance_morning(1)
        elif step < 25200 and step % 60 == 0:
            rebalance_morning(2)   
        
        if step == 0:
            depot_main1_anz = 0
            depot_pasing1_anz = 0
            depot_pasing2_anz = 0
            for i in range(1, 451):
                if i < 441:
                    prt_temp = createShuttle("depot_main1", count)
                    depot_main1_anz += 1 
                elif i < 446:              
                    prt_temp = createShuttle("depot_pasing1", count)
                    depot_pasing1_anz += 1
                elif i < 451:              
                    prt_temp = createShuttle("depot_pasing2", count)
                    depot_pasing2_anz += 1
                prt_shuttle.append(prt_temp)
                count += 1
            print(depot_main1_anz, end=', ')
            print(depot_pasing1_anz, end=', ')
            print(depot_pasing2_anz)


        
        if (step+1)%1000 == 0:
            stop = datetime.now()
            td = (stop - start).total_seconds() * 10**3
            print(f"The time of execution at step {step} : {td:.03f}ms")
            sim_stop = datetime.now()
            sim_td = (sim_stop - sim_start).total_seconds() * 10**3
            print(f"The time of execution total at step {step} : {sim_td:.03f}ms")
    
        step += 1

    traci.close()

start_sumo_background_task()

