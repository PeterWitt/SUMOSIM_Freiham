import traci

shuttle_rebalanced = {"pasing1": [], "pasing2": [], "freiham1": []}
prt_shuttle = []
shuttle_free_main_park = []


def create_shuttle(route, num):
    ########################
    # create_shuttle inserts shuttle into the simulation.
    # string route: defines insertion point
    # int num: defines the number of vehicle 
    ########################

    global shuttle_rebalanced
    global prt_shuttle

    traci.vehicle.add(f'taxiV{num}', route, typeID='shuttle', depart='now', departPos='free', departSpeed="avg",
                      line='taxi')

    match route:
        case "depot_main1":
            traci.vehicle.setParkingAreaStop(f'taxiV{num}', "main_park1", duration=999999, flags=1)
        case "depot_pasing1":
            traci.vehicle.setParkingAreaStop(f'taxiV{num}', "pasing_park1", duration=999999, flags=1)
            shuttle_rebalanced["pasing1"].append(f'taxiV{num}')
        case "depot_pasing2":
            traci.vehicle.setParkingAreaStop(f'taxiV{num}', "pasing_park2", duration=999999, flags=1)
            shuttle_rebalanced["pasing2"].append(f'taxiV{num}')

    prt_shuttle.append(f'taxiV{num}')


def rebalancing_main():
    ########################
    # rebalancing_main is the main rebalancing methode. 
    # Any free vehicle that has not yet been reallocated will be directed to the main park.
    # Vehicles that have dropped off passengers at Pasing station are directed to the buffer there.
    ########################

    global prt_shuttle
    global shuttle_rebalanced
    global shuttle_free_main_park

    shuttle_free_main_park = []
    shuttle_to_be_rebalanced = []

    # get all shuttles that are not parked or rebalanced, but are free/ideling
    shuttle_parked_main_park = traci.parkingarea.getVehicleIDs("main_park1")
    free_shuttle = traci.vehicle.getTaxiFleet(0)
    shuttle_parked = shuttle_parked_main_park + traci.parkingarea.getVehicleIDs(
        "pasing_park1") + traci.parkingarea.getVehicleIDs("pasing_park2")
    shuttle_free_not_rebalanced = [shuttle for shuttle in free_shuttle if
                                   shuttle not in shuttle_rebalanced["pasing1"] and shuttle not in shuttle_rebalanced[
                                       "pasing2"] and shuttle not in shuttle_rebalanced["freiham1"]]
    shuttle_to_be_rebalanced = [shuttle for shuttle in shuttle_free_not_rebalanced if shuttle not in shuttle_parked]

    # rebalance vehicles
    # if the vehicle dropped off the customer in Pasing (dropoff_lane1 or dropoff_lane2), the vehicle should try to park in Pasing puffer
    # if the vehicle is not at the Pasing station, it should return to main park
    for shuttle_name in shuttle_to_be_rebalanced:
        if not traci.vehicle.isStoppedParking(shuttle_name):
            shuttle_edge = traci.lane.getEdgeID(
                traci.vehicle.getLaneID(shuttle_name) if traci.vehicle.getLaneID(shuttle_name) != '' else "parked")
            try:
                if shuttle_edge in ["E21", "dropoff_lane2"]:
                    traci.vehicle.changeTarget(shuttle_name,
                                               traci.lane.getEdgeID(traci.parkingarea.getLaneID("pasing_park2")))
                    traci.vehicle.setParkingAreaStop(shuttle_name, "pasing_park2", duration=999999, flags=1)
                    shuttle_rebalanced["pasing2"].append(shuttle_name)
                elif shuttle_edge in ["E22", "dropoff_lane1"]:
                    traci.vehicle.changeTarget(shuttle_name,
                                               traci.lane.getEdgeID(traci.parkingarea.getLaneID("pasing_park1")))
                    traci.vehicle.setParkingAreaStop(shuttle_name, "pasing_park1", duration=999999, flags=1)
                    shuttle_rebalanced["pasing1"].append(shuttle_name)
                else:
                    traci.vehicle.changeTarget(shuttle_name,
                                               traci.lane.getEdgeID(traci.parkingarea.getLaneID(f"main_park1")))
                    traci.vehicle.setParkingAreaStop(shuttle_name, "main_park1", duration=999999, flags=1)
            except traci.exceptions.TraCIException as e:
                print(e)
                continue

                # get all vehicles parked in the main parking lot are free and not rebalanced
    shuttle_free_main_park = [shuttle for shuttle in shuttle_parked_main_park if shuttle in shuttle_free_not_rebalanced]


def rebalancing_helper():
    ########################
    # rebalancing_helper supplies Pasing Station with buffer vehicles. 
    # The number of vehicles dispatched to Pasing is exactly equal to the number of free slots, minus those already rebalanced.  
    # Vehicles are dispatched from the main park that are free and not already rebalanced.
    ########################

    global prt_shuttle
    global shuttle_rebalanced
    global shuttle_free_main_park

    # Check if vehicles have already arrived at the target and remove from rebalanced list.
    for park in ["pasing1", "pasing2", "freiham1"]:
        for shuttle in shuttle_rebalanced[park]:
            if traci.vehicle.isStoppedParking(shuttle) or traci.vehicle.getParameter(shuttle,
                                                                                     "device.taxi.state") != "0":
                shuttle_rebalanced[park].remove(shuttle)

    # Get capacity of station puffer
    num_vehicle_pasing1 = traci.parkingarea.getVehicleCount("pasing_park1")
    num_vehicle_pasing2 = traci.parkingarea.getVehicleCount("pasing_park2")
    empty_parkingspace_pasing1 = int(traci.simulation.getParameter("pasing_park1", "parkingArea.capacity")) - (
                num_vehicle_pasing1 + len(shuttle_rebalanced["pasing1"]))
    empty_parkingspace_pasing2 = int(traci.simulation.getParameter("pasing_park1", "parkingArea.capacity")) - (
                num_vehicle_pasing2 + len(shuttle_rebalanced["pasing2"]))

    # if places are available in pasing and enough free vehicles in main park, dispatch vehicles to the station
    if empty_parkingspace_pasing1 > 0:
        for i in range(0, empty_parkingspace_pasing1):
            if i >= 0 and i < len(shuttle_free_main_park):
                traci.vehicle.resume(shuttle_free_main_park[i])
                traci.vehicle.changeTarget(shuttle_free_main_park[i],
                                           traci.lane.getEdgeID(traci.parkingarea.getLaneID("pasing_park1")))
                traci.vehicle.setParkingAreaStop(shuttle_free_main_park[i], "pasing_park1", duration=999999, flags=1)
                shuttle_rebalanced["pasing1"].append(shuttle_free_main_park[i])
                shuttle_free_main_park.remove(shuttle_free_main_park[i])
            else:
                break

    if empty_parkingspace_pasing2 > 0:
        for i in range(empty_parkingspace_pasing1 + 1, empty_parkingspace_pasing1 + 1 + empty_parkingspace_pasing2):
            if i >= 0 and i < len(shuttle_free_main_park):
                traci.vehicle.resume(shuttle_free_main_park[i])
                traci.vehicle.changeTarget(shuttle_free_main_park[i],
                                           traci.lane.getEdgeID(traci.parkingarea.getLaneID("pasing_park2")))
                traci.vehicle.setParkingAreaStop(shuttle_free_main_park[i], "pasing_park2", duration=999999, flags=1)
                shuttle_rebalanced["pasing2"].append(shuttle_free_main_park[i])
                shuttle_free_main_park.remove(shuttle_free_main_park[i])
            else:
                break


def rebalance_low_demand(number, route="toggle_freiham1"):
    ########################
    # rebalance_low_demand is a strategy to compensate for low demand, e.g. at night.
    # Free and not rebalanced vehicles drive a route that provides coverage of an area.
    # int number: number of vehicles that should depart
    # string route: route the vehicle should take; default="toggle_freiham1"
    ########################

    global prt_shuttle
    global shuttle_free_main_park
    global shuttle_rebalanced

    # Redistribution a vehicle to main park when no customer is served
    for shuttle in shuttle_rebalanced["freiham1"]:
        if traci.vehicle.getLaneID(shuttle) not in ["depot_main1_0", "depot_main1_1"]:
            if traci.vehicle.getParameter(shuttle, "device.taxi.state") == "0":
                traci.vehicle.setParkingAreaStop(shuttle, "main_park1", duration=999999, flags=1)
            else:
                shuttle_rebalanced["freiham1"].remove(shuttle)

    # Set route to be driven for the specified number of vehicles and route
    for i in range(0, number):
        if i < len(shuttle_free_main_park):
            if traci.vehicle.isStoppedParking(shuttle_free_main_park[i]):
                traci.vehicle.resume(shuttle_free_main_park[i])
                try:
                    traci.vehicle.setRouteID(shuttle_free_main_park[i], route)
                    shuttle_rebalanced["freiham1"].append(shuttle_free_main_park[i])
                except:
                    shuttle_free_main_park.remove(shuttle_free_main_park[i])
            else:
                shuttle_free_main_park.remove(shuttle_free_main_park[i])
                print(shuttle_free_main_park[i] + "konnte nicht gerebalanced werden.")


def rebalance_basic(step, freqency_main, frequency_helper):
    ########################
    # rebalance_basic rebalanced vehicles according to freqence specifications
    # int step: simulation step
    # int freqency_main: frequency in which the main rebalancing should be executed. Specify every x seconds
    # int freqency_main: frequency in which the helper rebalancing should be executed. Specify every x seconds
    ########################
    if step % freqency_main == 0:
        rebalancing_main()
    if step % frequency_helper == 0:
        rebalancing_helper()


# TO-DO: Enter option for low-demand strategy
def rebalance_low_demand_timeline(time_number):
    ########################
    # rebalance_low_demand_timeline: create a distribution strategy
    # string time_number: Enter time interval (interval_start,interval_end), frequency, number and route of distributed cars seperated by ':'
    #                       To enter various pairs add them comma separeated
    #                       "intverval_start1:interval_end1:frequency1:number1:route1[,intverval_start2:interval_end2:frequency2:number2:route2]"
    #########################

    intervals = time_number.split(',')

    for interval in intervals:
        start, end, freq, number, route = interval.split(':')
        print(f"Interval: {start} to {end}; Every {freq} sek; Number {number} Route: {route}")
        i = 0
        while i < int(number):
            create_shuttle(route, count)
            i += 1
            print(count, end=" ")
            count += 1


def create_fleet(number_route):
    ########################
    # create_fleet: creation of a vehicle fleet
    # string number_route: Enter number of vehicle and route. It is possible to add more than one pair.
    #                       To enter various pairs add them comma separeated
    #                       "number1:route1[,number2:route2]"
    ########################
    count = 1

    fleets = number_route.split(',')

    for fleet in fleets:
        number, route = fleet.split(':')
        print(f"Number: {number} Route: {route}")
        i = 0
        while i < int(number):
            create_shuttle(route, count)
            i += 1
            count += 1