from math import sqrt
from random import shuffle, choice, randint
from time import perf_counter
import os.path

# ----------------------- Description of the program: --------------------------------- #
# This program solves the Vehicle Routing problem with Weak Cluster constraints
# using a Multi-Start + Iterative Variable Neibourhood Search algorithm with an Optimal Starting Solution

# Bellow you can see the methods that are used in this program, grouped by their purpose 
# and in the "__main__" section the code applied to a specific isntance

# Note: This algorimth takes the output of the CluVRPStrongV2.py algorithm as input
# so it needs to be ran first on the specific instance desired


# -------------------- Reading/Printing/Writing  Input/Output Methods ----------------- #

#Method that reads the input from the file:
def read_input(filename: str):
    with open (filename) as new_file:
        for _ in range(2):
            next(new_file)
        line = new_file.readline().strip().split(" ")
        n = int(line[-1])
        line = new_file.readline().strip().split(" ")
        k = int(line[-1])
        line = new_file.readline().strip().split(" ")
        r = int(line[-1])
        line = new_file.readline().strip().split(" ")
        Q = int(line[-1])
        for _ in range(2):
            next(new_file)
        points = []
        for _ in range(n):
            line = new_file.readline().strip().split(" ")
            points.append((int(line[1]), int(line[2])))
        next(new_file)
        clusters = []
        for _ in range(r):
            line = new_file.readline().strip().split(" ")
            cluster = []
            for point in line[1:-1]:
                #Subtract 1 to assure indexing starting at 0
                cluster.append(int(point)-1)
            clusters.append(cluster)
        demands = []
        next(new_file)
        for _ in range(r):
            line = new_file.readline().strip().split(" ")
            demands.append(int(line[-1]))
        next(new_file)
        print("Input red!")
    return n, k, r, Q, points, clusters, demands

#Method that reads the best strong constraint solution
def read_strong_solution(filename: str):
    best_cluster_orders = []
    best_vehicle_tours = []

    with open (filename[0] + "_StrongSolution.txt") as file:
        next(file)
        counter = 0

        for line in file:
            parts = line.strip().split(" ")
            if counter%2 == 0:
                clusters = [(int(n)-1) for n in parts]
                best_cluster_orders.append(clusters)
            else:
                customers = [(int(n)-1) for n in parts]
                best_vehicle_tours.append(customers)
            counter += 1

    return best_cluster_orders, best_vehicle_tours

#Method that prints the input to the screen (for potential verification purposes)
def print_input(n: int, k: int, r: int, Q: int, points: list[tuple], clusters: list[list], demands: list):
    print("Test input of the problem is:")
    print("n: ", n)
    print("k: ", k)
    print("r: ", r)
    print("Q: ", Q)
    print("Points:")
    for i in range (n):
        print(f"{i+1}: {points[i][0]} {points[i][1]}")
    print("Clusters:")
    for i in range (r):
        print(f"{i+1}: {clusters[i]}")
    print("Demands:")
    for i in range (r):
        print(f"{i+1}: {demands[i]}")
    print()

#Method that prints the best solution found to the screen
def printSolution(filename: str, time:float, nr_iterations: int, best_total_distance: int,  best_cluster_orders: list[list], best_vehicle_tours: list[list], demands:list):
    print()
    print(f"After {nr_iterations} iterations of the VNS algorithm")
    print(f"The best solution found for instance {filename} of the Weak variant has distance:")
    print(best_total_distance)
    print()
    print("The solution corresponding to this result is:")
    print()
    for i in range(len(best_cluster_orders)):
        print(f"Vehicle {i+1}: ", end ="")
        print(' '.join([str(n+1) for n in best_cluster_orders[i]]))
        print(f"Total demand: {sum_demands(best_cluster_orders[i], demands)}")
        print("Tour: |", end ="")
        print(' '.join([str(n+1) for n in best_vehicle_tours[i]]), end="")
        print("|")
        print()
    print("The algorithm took:")
    print(f"{time :.2f} seconds")
    print()

#Method that updates the file with best solutions if a better one was found
def update_best_solution(filename: str, best_total_distance: int):
    if not os.path.isfile("best_we_found_weak.txt"):
        instances = "ABCDEFGHIJK"
        with open("best_we_found_weak.txt", "w") as new_file:
            for letter in instances:
                line = letter + " 10000"
                new_file.write(line+"\n")

    with open ("best_we_found_weak.txt") as file:
        best_scores = {}

        for line in file:
            parts = line.strip().split(" ")
            best_scores[parts[0]] = int(parts[1])

        if best_scores[filename[0]] > best_total_distance:
            best_scores[filename[0]] = best_total_distance
            print("New best result found!")

    with open("best_we_found_weak.txt", "w") as my_file:
        for instance, distance in best_scores.items():
            line = instance + " " + str(distance)
            my_file.write(line+"\n")

#Method that writes out the solution to a file
def write_solution(filename: str, best_total_distance: int, best_cluster_orders: list[list], best_vehicle_tours: list[list]):
    if not os.path.isfile(filename[0] + "_WeakSolution.txt"):
        with open(filename[0] + "_WeakSolution.txt", "w") as new_file:
            line = str(best_total_distance)
            new_file.write(line+"\n")
            for i in range(len(best_cluster_orders)):
                line = ""
                line += ' '.join([str(n+1) for n in best_cluster_orders[i]])
                new_file.write(line+"\n")
                line = ""
                line += ' '.join([str(n+1) for n in best_vehicle_tours[i]])
                new_file.write(line+"\n")
        
    else:
        with open(filename[0] + "_WeakSolution.txt", "r") as my_file:
            line = my_file.readline().strip()
            past_distance = int(line)

        if best_total_distance < past_distance:
            with open(filename[0] + "_WeakSolution.txt", "w") as new_file:
                line = str(best_total_distance)
                new_file.write(line+"\n")
                for i in range(len(best_cluster_orders)):
                    line = ""
                    line += ' '.join([str(n+1) for n in best_cluster_orders[i]])
                    new_file.write(line+"\n")
                    line = ""
                    line += ' '.join([str(n+1) for n in best_vehicle_tours[i]])
                    new_file.write(line+"\n") 


# -------------------- Methods that construct the initial solution -------------------- #

#Method that computes the distances between the points and returns them in adjancencency matrix form:
def distance_matrix(n: int, points: list[tuple]):
    distance_matrix = [[0] * n for _ in range(n)]
    for i in range(n):
        for j in range(n):
            distance_matrix[i][j] = round(sqrt((points[i][0] - points[j][0]) **2 + (points[i][1] - points[j][1]) **2))
    return distance_matrix
    
#Method that computes the current sum of demands for a list of clusters
def sum_demands(cluster_list:list, demands:list):
    sum = 0
    for cluster in cluster_list:
        sum += demands[cluster]
    return sum

#Method that computes the total distance of the current solution:
def total_distance(distances: list[list], vehicle_tours: list[list]):
    total_distance = 0
    for vehicle in vehicle_tours:
        for i in range(len(vehicle)-1):
            total_distance += distances[vehicle[i]][vehicle[i+1]]
        
        total_distance += distances[0][vehicle[0]]
        total_distance += distances[0][vehicle[-1]]

    return total_distance

#Method that performs a first-fit heuristic for a bin packing problem, until exactly k bins are used 
def first_fit(k: int, Q: int, demands: list):
    copy_demands = demands.copy()
    shuffle(copy_demands)
    bins = []

    while len(bins) != k:
        bins = []
        shuffle(copy_demands)
        bins.append([])
        for number in copy_demands:
            added = False
            for bin in bins:
                if sum(bin) + number <= Q:
                    bin.append(number)
                    added = True
                    break
            if not added:
                new_bin = []
                new_bin.append(number)
                bins.append(new_bin)

    return bins

#Method that uses the bin allocation from above to create an initial allocation of clusters to vehicle tours
def clusters_to_vehicles(k: int, Q: int, demands: list):
    bins = first_fit(k, Q, demands)
    vehicles = []
    copy_demands = demands.copy()

    for bin in bins:
        vehicle = []
        for number in bin:
            indexes = []
            for i in range(len(copy_demands)):
                if copy_demands[i] == number:
                    indexes.append(i)
            index = choice(indexes)
            copy_demands[index] = -1
            vehicle.append(index)
        vehicles.append(vehicle)

    for vehicle in vehicles:
        shuffle(vehicle)

    return vehicles  
        
#Method that generates the initial solution
def generate_solution(clusters: list[list], demands: list):
    cluster_orders = clusters_to_vehicles(k, Q, demands)

    vehicle_tours = []
    for vehicle in cluster_orders:
        vehicle_tour = []
        for cluster in vehicle:
            for customer in clusters[cluster]:
                vehicle_tour.append(customer)
        shuffle(vehicle_tour)
        vehicle_tours.append(vehicle_tour)


    return cluster_orders, vehicle_tours


# ------------------- Methods that implement the moves of the VNS --------------------- #

#Method that implements move 1
def move1(distances: list[list], vehicle_tours: list[list]):
    for vehicle in vehicle_tours:
        best_distance = total_distance(distances, vehicle_tours)
        index1 = 0
        index2 = 0
        for i in range(len(vehicle)):
            for j in range(len(vehicle)):
                swap_in_list(vehicle, i, j)
                if total_distance(distances, vehicle_tours) < best_distance:
                    best_distance = total_distance(distances, vehicle_tours)
                    index1 = i
                    index2 = j
                swap_in_list(vehicle, i, j)

        swap_in_list(vehicle, index1, index2)
                
#Method that implements move 2
def move2(distances: list[list], vehicle_tours: list[list]):
    for vehicle in vehicle_tours:
        best_distance = total_distance(distances, vehicle_tours)
        index1 = 0
        index2 = 0
        length = 1
        for i in range(len(vehicle)):
            for j in range(len(vehicle)):
                for k in range(1, len(vehicle)+1):
                    if max(i + k, j + k) <= len(vehicle):
                        move_in_list(vehicle, i, j, k)
                        if total_distance(distances, vehicle_tours) < best_distance:
                            best_distance = total_distance(distances, vehicle_tours)
                            index1 = i
                            index2 = j
                            length = k
                        move_in_list(vehicle, j, i, k)

        move_in_list(vehicle, index1, index2, length)

#Method that implements move 3
def move3(Q: int, demands: list, distances: list[list], clusters: list[list], cluster_orders: list[list], vehicle_tours: list[list]):
    best_distance = total_distance(distances, vehicle_tours)
    old_vehicle = 0
    new_vehicle = 0
    position_cluster = 0
    position_customer = 0
    length = 1
    improvement = False

    for i in range(len(cluster_orders)):
        for j in range(len(cluster_orders)):
            if i != j:
                for k in range(len(cluster_orders[i])):
                    for m in range(1, len(cluster_orders[i])):
                        if m + k < len(cluster_orders[i]): 
                            sum = sum_demands(cluster_orders[j], demands)
                            for t in range(m):
                                sum += demands[cluster_orders[i][k+t]]
                            if sum <= Q:
                                for l in range(len(vehicle_tours[j])+1):
                                    copy_vehicle_tours = copy_lists_of_lists(vehicle_tours)
                                    aux_list = []
                                    for t in range(m):
                                        temp = remove_from_list(copy_vehicle_tours[i], clusters[cluster_orders[i][k+t]])
                                        for item in temp:
                                            aux_list.append(item)
                                    insert_list_in_list(copy_vehicle_tours[j], aux_list, l)
                                    if total_distance(distances, copy_vehicle_tours) < best_distance:
                                        best_distance = total_distance(distances, copy_vehicle_tours)
                                        old_vehicle = i
                                        new_vehicle = j
                                        position_cluster = k
                                        position_customer = l
                                        length = m
                                        improvement = True
                                        
    if improvement:
        aux_list = []
        for t in range(length):
            temp = remove_from_list(vehicle_tours[old_vehicle], clusters[cluster_orders[old_vehicle][position_cluster+t]])
            for item in temp:
                aux_list.append(item)
        insert_list_in_list(vehicle_tours[new_vehicle], aux_list, position_customer)
        move_between_lists(cluster_orders[old_vehicle], cluster_orders[new_vehicle], position_cluster, 0, length)

#Method that implements move 4
def move4(Q: int, demands: list, distances: list[list], clusters: list[list], cluster_orders: list[list], vehicle_tours: list[list]):
    vehicle1 = 0
    vehicle2 = 0
    cluster_index1 = 0
    cluster_index2 = 0
    tour_index1 = 0
    tour_index2 = 0
    best_distance = total_distance(distances, vehicle_tours)
    improvement = False

    for i in range(len(cluster_orders)):
        for j in range(len(cluster_orders)):
            if i != j:
                for k in range(len(cluster_orders[i])):
                    for l in range(len(cluster_orders[j])):
                        sum1 = sum_demands(cluster_orders[i], demands) - demands[cluster_orders[i][k]] + demands[cluster_orders[j][l]]
                        sum2 = sum_demands(cluster_orders[j], demands) - demands[cluster_orders[j][l]] + demands[cluster_orders[i][k]]
                        if sum1 <= Q and sum2 <= Q:
                            for i1 in range(len(vehicle_tours[i])+1):
                                for j1 in range(len(vehicle_tours[j])+1):
                                    copy_vehicle_tours = copy_lists_of_lists(vehicle_tours)
                                    aux_list1 = remove_from_list(copy_vehicle_tours[i], clusters[cluster_orders[i][k]])
                                    aux_list2 = remove_from_list(copy_vehicle_tours[j], clusters[cluster_orders[j][l]])
                                    insert_list_in_list(copy_vehicle_tours[i], aux_list2, i1)
                                    insert_list_in_list(copy_vehicle_tours[j], aux_list1, j1)
                                    if total_distance(distances, copy_vehicle_tours) < best_distance:
                                        best_distance = total_distance(distances, copy_vehicle_tours)
                                        vehicle1 = i
                                        vehicle2 = j
                                        cluster_index1 = k
                                        cluster_index2 = l
                                        tour_index1 = i1
                                        tour_index2 = j1
                                        improvement = True

    if improvement:
        aux_list1 = remove_from_list(vehicle_tours[vehicle1], clusters[cluster_orders[vehicle1][cluster_index1]])
        aux_list2 = remove_from_list(vehicle_tours[vehicle2], clusters[cluster_orders[vehicle2][cluster_index2]])
        insert_list_in_list(vehicle_tours[vehicle1], aux_list2, tour_index1)
        insert_list_in_list(vehicle_tours[vehicle2], aux_list1, tour_index2)
        swap_between_lists(cluster_orders[vehicle1], cluster_orders[vehicle2], cluster_index1, cluster_index2)

# Method that performs a perturbation on the current solution
def perturbation(cluster_orders: list[list], vehicle_tours: list[list], demands:list):
    
    perturbated = False
    while not perturbated:

        i = randint(0, len(cluster_orders)-1)
        j = randint(0, len(cluster_orders)-1)
        if i != j:
            k = randint(0, len(cluster_orders[i])-1)
            l = randint(0, len(cluster_orders[j])-1)
            sum1 = sum_demands(cluster_orders[i], demands) - demands[cluster_orders[i][k]] + demands[cluster_orders[j][l]]
            sum2 = sum_demands(cluster_orders[j], demands) - demands[cluster_orders[j][l]] + demands[cluster_orders[i][k]]
            if sum1 <= Q and sum2 <= Q:
                aux_list1 = remove_from_list(vehicle_tours[i], clusters[cluster_orders[i][k]])
                aux_list2 = remove_from_list(vehicle_tours[j], clusters[cluster_orders[j][l]])
                insert_list_in_list(vehicle_tours[i], aux_list2, 0)
                insert_list_in_list(vehicle_tours[j], aux_list1, 0)
                swap_between_lists(cluster_orders[i], cluster_orders[j], k, l)
                
                perturbated = True
                break

# -------------------- Helper Methods for immplementing the moves --------------------- #

#Method that swaps two items in a list
def swap_in_list(list: list, index1: int, index2:int):
    value1 = list[index1]
    value2 = list[index2]
    list[index1] = value2
    list[index2] = value1

#Method that moves t consecutive items along the list
def move_in_list(list: list, index1: int, index2:int, t: int):
    temp = []
    for _ in range(t):
        temp.append(list.pop(index1))
    temp.reverse()
    for i in range(t):
        list.insert(index2, temp[i])

#Method that swaps two elements between 2 lists
def swap_between_lists(list1: list, list2: list, index1: int, index2: int):
    value1 = list1[index1]
    value2 = list2[index2]
    list1[index1] = value2
    list2[index2] = value1

#Method that moves t consecutive items from a list to another in a specified postion
def move_between_lists(list1: list, list2: list, index1: int, index2: int, t: int):
    temp = []
    for _ in range(t):
        temp.append(list1.pop(index1))
    temp.reverse()
    for i in range(t):
        list2.insert(index2, temp[i])

#method that the removes the the elements of a list that are contained in another list and returns them
def remove_from_list(list1: list, list2: list):
    new_list = []
    for item in list1:
        if item in list2:
            new_list.append(item)
    for item in new_list:
        list1.remove(item)

    return new_list

#Method that inserts a list of items into a larger list at a specific instance 
def insert_list_in_list(list1: list, list2: list, index: int):
    list2.reverse()
    for item in list2:
        list1.insert(index, item)

#Method that returns a copy for a list of lists
def copy_lists_of_lists(my_list: list[list]):
    new_list = []
    for item in my_list:
        temp = item.copy()
        new_list.append(temp)

    return new_list


# ---------------------------------- Main Methods -------------------------------------- #

#Method that applies the Multi-Start + Iterative Variable Neigbourhood Search:
def VNS(n_iter: int, Q: int, distances: list[list], clusters: list[list], demands: list, start_cluster_orders: list[list], start_vehicle_tours: list[list]):
    start_time = perf_counter()
    seconds_1 = False
    seconds_10 = False
    seconds_30 = False
    seconds_60 = False
    seconds_300 = False
    seconds_1800 = False
    m = n_iter // 10
    
    total_distance_traveled = total_distance(distances, start_vehicle_tours)
    best_total_distance = total_distance_traveled
    best_cluster_orders = copy_lists_of_lists(start_cluster_orders)
    best_vehicle_tours = copy_lists_of_lists(start_vehicle_tours) 

    for i in range(n_iter):

        cluster_orders = copy_lists_of_lists(start_cluster_orders)
        vehicle_tours = copy_lists_of_lists(start_vehicle_tours)
        perturbation(cluster_orders, vehicle_tours, demands)
        total_distance_traveled = total_distance(distances, vehicle_tours)
        
        improvement = True
        while improvement:
            improvement = False

            improve = True
            while improve:
                improve = False
                move2(distances, vehicle_tours)
                new_distance = total_distance(distances, vehicle_tours)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True

            improve = True
            while improve:
                improve = False
                move1(distances, vehicle_tours)
                new_distance = total_distance(distances, vehicle_tours)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True

            improve = True        
            while improve:
                improve = False
                move4(Q, demands, distances, clusters, cluster_orders, vehicle_tours)
                new_distance = total_distance(distances, vehicle_tours)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True

            improve = True
            while improve:
                improve = False
                move3(Q, demands, distances, clusters, cluster_orders, vehicle_tours)
                new_distance = total_distance(distances, vehicle_tours)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True
                
            if total_distance_traveled < best_total_distance:
                best_total_distance = total_distance(distances, vehicle_tours)
                best_cluster_orders = copy_lists_of_lists(cluster_orders)
                best_vehicle_tours = copy_lists_of_lists(vehicle_tours)
                if seconds_30:
                    print(f"After {i+1} iterations, {perf_counter()-start_time:.2f} seconds, the NEW best solution found has total distance: {best_total_distance}")

        if perf_counter() - start_time > 1 and not seconds_1:
            seconds_1 = True
            print(f"After 1 second, {i+1} iterations, best solution found has total distance:")
            print(best_total_distance)

        if perf_counter() - start_time > 10 and not seconds_10:
            seconds_10 = True
            print(f"After 10 seconds, {i+1} iterations, best solution found has total distance:")
            print(best_total_distance)

        if perf_counter() - start_time > 30 and not seconds_30:
            seconds_30 = True
            print(f"After 30 seconds, {i+1} iterations, best solution found has total distance:")
            print(best_total_distance)

        if perf_counter() - start_time > 60 and not seconds_60:
            seconds_60 = True
            print(f"After 60 seconds, {i+1} iterations, best solution found has total distance:")
            print(best_total_distance)
            print()

        if perf_counter() - start_time > 300 and not seconds_300:
            seconds_300 = True
            print()
            print(f"After 300 seconds(5 minutes), {i+1} iterations, best solution found has total distance:")
            print(best_total_distance)
            print()

        if perf_counter() - start_time > 1800 and not seconds_1800:
            seconds_1800 = True
            print()
            print(f"After 1800 seconds(30 minutes), {i+1} iterations, best solution found has total distance:")
            print(best_total_distance)
            print()

        if i%m == m-1 and seconds_60:
            print(f"After {i+1} iterations, {perf_counter()-start_time:.2f} seconds, the best solution found has total distance: {best_total_distance}")

    return best_total_distance, best_cluster_orders, best_vehicle_tours



if __name__ == "__main__":

    #Update the name of the file to switch to a different instance
    filename = "A.gvrp"
    #Read the input from the file
    n, k, r, Q, points, clusters, demands = read_input(filename)
    distances = distance_matrix(n, points)
    start_cluster_orders, start_vehicle_tours = read_strong_solution(filename)

    #Printing the input(for potential verification purposes)   
    #print_input(n, k, r, Q, points, clusters, demands)

    #The number of iterations can be updated here
    nr_iterations = 100

    start_time = perf_counter()
    best_total_distance, best_cluster_orders, best_vehicle_tours = VNS(nr_iterations, Q, distances, clusters, demands, start_cluster_orders, start_vehicle_tours)
    end_time = perf_counter()
    time = end_time - start_time

    #Print the best solution 
    printSolution(filename, time, nr_iterations, best_total_distance,  best_cluster_orders, best_vehicle_tours, demands)

    #Update the file containing the best distances found so far
    update_best_solution(filename, best_total_distance)

    #Update the solution written down into a file if it is better
    write_solution(filename, best_total_distance, best_cluster_orders, best_vehicle_tours)
