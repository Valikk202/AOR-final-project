from math import sqrt
from random import shuffle, choice
from time import perf_counter
import os.path

# ----------------------- Description of the program: --------------------------------- #
# This program solves the Vehicle Routing problem with Strong Cluster constraints
# using a Multi-Start Variable Neibourhood Search algorithm 

# Bellow you can see the methods that are used in this program, grouped by their purpose 
# and in the "__main__" section the code applied to a specific instance


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
def printSolution(filename: str, time:float, nr_iterations: int, best_total_distance: int,  best_cluster_orders: list[list], best_customer_orders: dict[list], demands:list):
    print()
    print(f"After {nr_iterations} iterations of the VNS algorithm")
    print(f"The best solution found for instance {filename} of the Strong variant has distance:")
    print(best_total_distance)
    print()
    print("The solution corresponding to this result is:")
    print()
    for i in range(len(best_cluster_orders)):
        print(f"Vehicle {i+1}: ", end ="")
        print(' '.join([str(n+1) for n in best_cluster_orders[i]]))
        print(f"Total demand: {sum_demands(best_cluster_orders[i], demands)}")
        print("Tour: |", end ="")
        for cluster in best_cluster_orders[i]:
            print(' '.join([str(n+1) for n in best_customer_orders[cluster]]), end="")
            print("|", end="")
        print()
        print()
    print("The algorithm took:")
    print(f"{time :.2f} seconds")
    print()

#Method that updates the file with best solutions if a better one was found
def update_best_solution(filename: str, best_total_distance: int):
    if not os.path.isfile("best_we_found_strong.txt"):
        instances = "ABCDEFGHIJK"
        with open("best_we_found_strong.txt", "w") as new_file:
            for letter in instances:
                line = letter + " 10000"
                new_file.write(line+"\n")

    with open ("best_we_found_strong.txt") as file:
        best_scores = {}

        for line in file:
            parts = line.strip().split(" ")
            best_scores[parts[0]] = int(parts[1])

        if best_scores[filename[0]] > best_total_distance:
            best_scores[filename[0]] = best_total_distance
            print("New best result found!")

    with open("best_we_found_strong.txt", "w") as my_file:
        for instance, distance in best_scores.items():
            line = instance + " " + str(distance)
            my_file.write(line+"\n")  

#Method that writes out the solution to a file
def write_solution(filename: str, best_total_distance: int, best_cluster_orders: list[list], best_customer_orders: dict[list]):
    if not os.path.isfile(filename[0] + "_StrongSolution.txt"):
        with open(filename[0] + "_StrongSolution.txt", "w") as new_file:
            line = str(best_total_distance)
            new_file.write(line+"\n")
            for i in range(len(best_cluster_orders)):
                line = ""
                line += ' '.join([str(n+1) for n in best_cluster_orders[i]])
                new_file.write(line+"\n")
                line = ""
                for cluster in best_cluster_orders[i]:
                    line += ' '.join([str(n+1) for n in best_customer_orders[cluster]])
                    line += " "
                line = line[:-1]
                new_file.write(line+"\n")
        
    else:
        with open(filename[0] + "_StrongSolution.txt", "r") as my_file:
            line = my_file.readline().strip()
            past_distance = int(line)

        if best_total_distance < past_distance:
            with open(filename[0] + "_StrongSolution.txt", "w") as file:
                line = str(best_total_distance)
                file.write(line+"\n")
                for i in range(len(best_cluster_orders)):
                    line = ""
                    line += ' '.join([str(n+1) for n in best_cluster_orders[i]])
                    file.write(line+"\n")
                    line = ""
                    for cluster in best_cluster_orders[i]:
                        line += ' '.join([str(n+1) for n in best_customer_orders[cluster]])
                        line += " "
                    line = line[:-1]
                    file.write(line+"\n")


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
def total_distance(distances: list[list], cluster_orders: list[list], customer_orders: dict):
    total_distance = 0
    for vehicle_route in cluster_orders:
        for cluster in vehicle_route:
            for i in range(len(customer_orders[cluster])-1):
                total_distance += distances[customer_orders[cluster][i]][customer_orders[cluster][i+1]]

        for i in range(len(vehicle_route)-1):
            total_distance += distances[customer_orders[vehicle_route[i]][-1]][customer_orders[vehicle_route[i+1]][0]]

        total_distance += distances[0][customer_orders[vehicle_route[0]][0]]
        total_distance += distances[0][customer_orders[vehicle_route[-1]][-1]]

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
    customer_orders = {}
    for i in range(len(clusters)):
        copy = clusters[i].copy()
        shuffle(copy)
        customer_orders[i] = copy.copy()

    cluster_orders = clusters_to_vehicles(k, Q, demands)

    return cluster_orders, customer_orders

# ------------------- Methods that implement the moves of the VNS --------------------- #

#Method that implements move 1
def move1(distances: list[list], cluster_orders: list[list], customer_orders: dict):
    for customers in customer_orders.values():
        best_distance = total_distance(distances, cluster_orders, customer_orders)
        index1 = 0
        index2 = 0
        for i in range (len(customers)):
            for j in range (len(customers)):
                swap_in_list(customers, i, j)
                if total_distance(distances, cluster_orders, customer_orders) < best_distance:
                    best_distance = total_distance(distances, cluster_orders, customer_orders)
                    index1 = i
                    index2 = j
                swap_in_list(customers, i, j)

        swap_in_list(customers, index1, index2)
                
#Method that implements move 2
def move2(distances: list[list], cluster_orders: list[list], customer_orders: dict):
    for customers in customer_orders.values():
        best_distance = total_distance(distances, cluster_orders, customer_orders)
        index1 = 0
        index2 = 0
        length = 1
        for i in range (len(customers)):
            for j in range (len(customers)):
                for k in range(1, len(customers)+1):
                    if max(i + k, j + k) <= len(customers):    
                        move_in_list(customers, i, j, k)
                        if total_distance(distances, cluster_orders, customer_orders) < best_distance:
                            best_distance = total_distance(distances, cluster_orders, customer_orders)
                            index1 = i
                            index2 = j
                            length = k
                        move_in_list(customers, j, i, k)

        move_in_list(customers, index1, index2, length)

#Method that implements move 3
def move3(distances: list[list], cluster_orders: list[list], customer_orders: dict):
    for vehicle_route in cluster_orders:
        best_distance = total_distance(distances, cluster_orders, customer_orders)
        index1 = 0
        index2 = 0
        for i in range (len(vehicle_route)):
            for j in range (len(vehicle_route)):
                swap_in_list(vehicle_route, i, j)
                if total_distance(distances, cluster_orders, customer_orders) < best_distance:
                    best_distance = total_distance(distances, cluster_orders, customer_orders)
                    index1 = i
                    index2 = j
                swap_in_list(vehicle_route, i, j)

        swap_in_list(vehicle_route, index1, index2)

#Method that implements move 4
def move4(distances: list[list], cluster_orders: list[list], customer_orders: dict):
    for vehicle_route in cluster_orders:
        best_distance = total_distance(distances, cluster_orders, customer_orders)
        index1 = 0
        index2 = 0
        length = 1
        for i in range (len(vehicle_route)):
            for j in range (len(vehicle_route)):
                for k in range (1, len(vehicle_route)+1):
                    if max(i + k, j + k) <= len(vehicle_route):
                        move_in_list(vehicle_route, i, j, k)
                        if total_distance(distances, cluster_orders, customer_orders) < best_distance:
                            best_distance = total_distance(distances, cluster_orders, customer_orders)
                            index1 = i
                            index2 = j
                            length = k
                        move_in_list(vehicle_route, j, i, k)

        move_in_list(vehicle_route, index1, index2, length)

#Method that implements move 5
def move5(Q: int, demands: list, distances: list[list], cluster_orders: list[list], customer_orders: dict):
    best_distance = total_distance(distances, cluster_orders, customer_orders)
    old_vehicle = 0
    new_vehicle = 0
    old_postion = 0
    new_position = 0
    length = 1

    for i in range(len(cluster_orders)):
        for j in range(len(cluster_orders[i])):
            for k in range(len(cluster_orders)): 
                if k != i:
                    for l in range(len(cluster_orders[k])):
                        for m in range(1, len(cluster_orders[i])+1):
                            if m + j <= len(cluster_orders[i]):
                                sum = sum_demands(cluster_orders[k], demands)
                                for t in range(m):
                                    sum += demands[cluster_orders[i][j+t]]
                                if sum <= Q:
                                    move_between_lists(cluster_orders[i], cluster_orders[k], j, l, m)
                                    if total_distance(distances, cluster_orders, customer_orders) < best_distance:
                                        best_distance = total_distance(distances, cluster_orders, customer_orders)
                                        old_vehicle = i
                                        new_vehicle = k
                                        old_postion = j
                                        new_position = l
                                        length = m
                                    move_between_lists(cluster_orders[k], cluster_orders[i], l, j, m)

    move_between_lists(cluster_orders[old_vehicle], cluster_orders[new_vehicle], old_postion, new_position, length)

#Method that implements move 6
def move6(Q: int, demands: list, distances: list[list], cluster_orders: list[list], customer_orders: dict):
    vehicle1 = 0
    vehicle2 = 0
    cluster_index1 = 0
    cluster_index2 = 0
    best_distance = total_distance(distances, cluster_orders, customer_orders)

    for i in range(len(cluster_orders)):
        for j in range(len(cluster_orders)):
            if i != j:
                for k in range(len(cluster_orders[i])):
                    for l in range(len(cluster_orders[j])):
                        sum1 = sum_demands(cluster_orders[i], demands) - demands[cluster_orders[i][k]] + demands[cluster_orders[j][l]]
                        sum2 = sum_demands(cluster_orders[j], demands) - demands[cluster_orders[j][l]] + demands[cluster_orders[i][k]]
                        if sum1 <= Q and sum2 <= Q:
                            swap_between_lists(cluster_orders[i], cluster_orders[j], k, l)
                            if total_distance(distances, cluster_orders, customer_orders) < best_distance:
                                best_distance = total_distance(distances, cluster_orders, customer_orders)
                                vehicle1 = i
                                vehicle2 = j
                                cluster_index1 = k
                                cluster_index2 = l
                            swap_between_lists(cluster_orders[i], cluster_orders[j], k, l)

    swap_between_lists(cluster_orders[vehicle1], cluster_orders[vehicle2], cluster_index1, cluster_index2)


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

#Method that returns a copy for a list of lists
def copy_lists_of_lists(my_list: list[list]):
    new_list = []
    for item in my_list:
        temp = item.copy()
        new_list.append(temp)

    return new_list

#method that returns a copy of a dictionary of lists:
def copy_dictionary(my_dict: dict[list]):
    new_dict = {}
    for key, value in my_dict.items():
        new_dict[key] = value.copy()

    return new_dict


# ---------------------------------- Main Method -------------------------------------- #

#Method that applies the Multi-Start Variable Neigbourhood Search:
def VNS(n_iter: int, Q: int, distances: list[list], clusters: list[list], demands: list):
    start_time = perf_counter()
    seconds_1 = False
    seconds_10 = False
    seconds_30 = False
    seconds_60 = False
    seconds_300 = False
    seconds_1800 = False
    m = n_iter // 10
    
    cluster_orders, customer_orders = generate_solution(clusters, demands)
    total_distance_traveled = total_distance(distances, cluster_orders, customer_orders)
    best_total_distance = total_distance_traveled
    best_cluster_orders = copy_lists_of_lists(cluster_orders)
    best_customer_orders = copy_dictionary(customer_orders) 

    for i in range(n_iter):

        cluster_orders, customer_orders = generate_solution(clusters, demands)
        total_distance_traveled = total_distance(distances, cluster_orders, customer_orders)
        
        improvement = True
        while improvement:
            improvement = False

            improve = True        
            while improve:
                improve = False
                move6(Q, demands, distances, cluster_orders, customer_orders)
                new_distance = total_distance(distances, cluster_orders, customer_orders)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True

            improve = True
            while improve:
                improve = False
                move5(Q, demands,distances, cluster_orders, customer_orders)
                new_distance = total_distance(distances, cluster_orders, customer_orders)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True

            improve = True
            while improve:
                improve = False
                move4(distances, cluster_orders, customer_orders)
                new_distance = total_distance(distances, cluster_orders, customer_orders)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True

            improve = True
            while improve:
                improve = False
                move3(distances, cluster_orders, customer_orders)
                new_distance = total_distance(distances, cluster_orders, customer_orders)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True

            improve = True
            while improve:
                improve = False
                move2(distances, cluster_orders, customer_orders)
                new_distance = total_distance(distances, cluster_orders, customer_orders)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True

            improve = True
            while improve:
                improve = False
                move1(distances, cluster_orders, customer_orders)
                new_distance = total_distance(distances, cluster_orders, customer_orders)
                if new_distance < total_distance_traveled:
                    total_distance_traveled = new_distance
                    improvement = True
                    improve = True
                
            if total_distance_traveled < best_total_distance:
                best_total_distance = total_distance(distances, cluster_orders, customer_orders)
                best_cluster_orders = copy_lists_of_lists(cluster_orders)
                best_customer_orders = copy_dictionary(customer_orders) 
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

    return best_total_distance, best_cluster_orders, best_customer_orders



if __name__ == "__main__":

    #Update the name of the file to switch to a different instance
    filename = "A.gvrp"
    #Read the input from the file
    n, k, r, Q, points, clusters, demands = read_input(filename)
    distances = distance_matrix(n, points)

    #Printing the input(for potential verification purposes)   
    #print_input(n, k, r, Q, points, clusters, demands)

    #The number of iterations can be updated here
    nr_iterations = 1000

    start_time = perf_counter()
    best_total_distance, best_cluster_orders, best_customer_orders = VNS(nr_iterations, Q, distances, clusters, demands)
    end_time = perf_counter()
    time = end_time - start_time

    #Print the best solution 
    printSolution(filename, time, nr_iterations, best_total_distance,  best_cluster_orders, best_customer_orders, demands)

    #Update the file containing the best distances found so far
    update_best_solution(filename, best_total_distance)

    #Update the solution written down into a file if it is better
    write_solution(filename, best_total_distance, best_cluster_orders, best_customer_orders)
