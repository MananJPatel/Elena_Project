import osmnx as ox
import networkx as nx
from heapq import *
import matplotlib.pyplot as plt
from collections import deque, defaultdict

class Algorithms:
    def __init__(self, G, x = 0.0, mode = "maximize"):
        """
        Initialize the class
        Params:
        G : Graph object
        x : percent over shortest distance
        mode : "maximize" or "minimize" elevation
        """
        self.G = G
        self.mode = mode
        self.x = x
        self.best = [[], 0.0, float('-inf'), 0.0]
        self.start_node, self.end_node = None, None

    def reload_graph(self, G):
        """
        Reinitialize current graph with "G"
        """
        self.G = G


    def getCost(self, n1, n2, mode = "normal"):
        """
        Different cost metrics between two nodes
        Params:
        n1 : node 1
        n2 : node 2
        mode : type of cost that we want
        Returns:
        Chosen cost between nodes n1 and n2
        """
        G = self.G
        if n1 is None or n2 is None : return
        if mode == "normal":
            try : return G.edges[n1, n2 ,0]["length"]
            except : return G.edges[n1, n2]["weight"]
        elif mode == "elevation-diff":
            # Difference in elevation of two nodes
            return G.nodes[n2]["elevation"] - G.nodes[n1]["elevation"]
        elif mode == "gain-only":
            return max(0.0, G.nodes[n2]["elevation"] - G.nodes[n1]["elevation"])
        elif mode == "drop-only":
            return max(0.0, G.nodes[n1]["elevation"] - G.nodes[n2]["elevation"])
        else:
            return abs(G.nodes[n1]["elevation"] - G.nodes[n2]["elevation"])
        


    def computeElevs(self, route, mode = "both", piecewise = False):
        """
        Given a list of node id's, compute the "cost" for that route
        Params:
        route : list of node ids
        mode : the cost metric that we want to aggregate (eg. distance between the nodes)
        piecewise : boolean variable to indicate if the piecewise cost between the nodes should be returned
        Returns:
        Total cost for route, Optional(Piecewise cost for route)
        """
        total = 0
        if piecewise : piecewiseElevs = []
        for i in range(len(route)-1):
            if mode == "both":
                diff = self.getCost(route[i],route[i+1],"elevation-diff")	
            elif mode == "gain-only":
                diff = self.getCost(route[i],route[i+1],"gain-only")
            elif mode == "drop-only":
                diff = self.getCost(route[i],route[i+1],"drop-only")
            elif mode == "normal":
                diff = self.getCost(route[i],route[i+1],"normal")
            total += diff
            if piecewise : piecewiseElevs.append(diff)
        if piecewise:
            return total, piecewiseElevs
        else:
            return total

    

    def getRoute(self, parent, dest):
        "returns the path given a parent mapping and the final dest"
        path = [dest]
        curr = parent[dest]
        while curr!=-1:
            path.append(curr)
            curr = parent[curr]
        return path[::-1]


    def verify_nodes(self):
        """
        Verify if the start/end nodes are None
        """
        if self.start_node is None or self.end_node is None:
            return False
        return True



    # Run the dijkstra algorithm
    def dijkstra(self, weight):
        """
        Finds the path that maximizes/minimizes absolute change in elevation between start and end nodes based on a heap impl.
        Params:
            weight : A list of two items. Defines how we wish to mark the cost between two nodes.
                    True/false value determines if the priority of the parent should be considered in the present node for heap. 
        Returns:
            currPriority, currDist, parent
            currPriority : priority of the target node in the heap
            currDist : total distance covered in the process of reaching the target node
            parent : a dictionary mapping between children and their parent. Useful for reconstructing the path from the target node.
        """
        if not self.verify_nodes() : return
        G, x, shortest, mode = self.G, self.x, self.shortest_dist, self.mode
        start_node, end_node = self.start_node, self.end_node
        q = [(0.0, 0.0, start_node)]
        seen = set()
        prior = {start_node: 0}
        
        parent = defaultdict(int)
        parent[start_node] = -1
        while q:
            currPriority, currDist, node = heappop(q)
            
            if node not in seen:
                seen.add(node)
                if node == end_node:
                    return currPriority, currDist, parent

                for nei in G.neighbors(node):
                    if nei in seen: continue
                    # get previous priority of node
                    prev = prior.get(nei, None)
                    # get normal distance between nodes
                    length = self.getCost(node, nei, "normal")
                    
                    # Update the distance between nodes
                    # If maximize, subtract the elevation difference from the actual distance
                    # If minimize, add the elevation difference to the actual distance
                    if mode == "maximize":
                        if weight[0] == 1:
                            next = length - self.getCost(node, nei, "elevation-diff")
                        elif weight[0] == 2:
                            next = (length - self.getCost(node, nei, "elevation-diff"))*length
                        elif weight[0] == 3:
                            next = length + self.getCost(node, nei, "drop-only")
                    else:
                        if weight[0] == 1:
                            next = length*0.1 + self.getCost(node, nei, "elevation-diff")
                        elif weight[0] == 2:
                            next = (length*0.1 + self.getCost(node, nei, "elevation-diff"))*length*0.1 
                        else: 
                            next = length*0.1 + self.getCost(node, nei, "gain-only")

                    # if true then consider priority of current node in the next
                    if weight[1]: 
                        next += currPriority
                    nextDist = currDist + length
                    if nextDist <= shortest*(1.0+x) and (prev is None or next < prev):
                        parent[nei] = node
                        prior[nei] = next
                        heappush(q, (next, nextDist, nei))        
        
        return None, None, None

    # Runs dijkstra with different weighing schemes for each edge
    def all_dijkstra(self):
        """
        Iteratively try out different weighting criterion for Dijkstra.
        Choose the one that returns the best result and store that in self.best
        """
        if not self.verify_nodes() : return
        start_node, end_node = self.start_node, self.end_node
        
        for weight in [[1, True], [2, True], [3, True], [1, False], [2, False], [3, False]]:
            _, currDist, parent = self.dijkstra(weight)
            
            if not currDist : continue
            
            route = self.getRoute(parent, end_node)
            elevDist, dropDist = self.computeElevs(route, "gain-only"), self.computeElevs(route, "drop-only")            
            if self.mode == "maximize":
                if (elevDist > self.best[2]) or (elevDist == self.best[2] and currDist < self.best[1]):
                    self.best = [route[:], currDist, elevDist, dropDist]
            else:
                if (elevDist < self.best[2]) or (elevDist == self.best[2] and currDist < self.best[1]):
                    self.best = [route[:], currDist,  elevDist, dropDist]
        
        return

    def shortest_path(self, start_location, end_location, x, mode = "maximize"):
        """
        Function to calculate the shortest path between the start_location and end_location.
        Params:
        start_location : tuple (lat, lng)
        end_location : tuple (lat, lng)
        x : how much more can we go above the shortest distance
        mode : minimize/maximize elevation
        log : log the results as the function runs
        Returns:
        L1
        both lists contain four items : [best route found, 
                                        total distance between the start and ending nodes of the best route, 
                                        total positive change in elevation,
                                        total negative change in elevation ]
        L1 returns the statistics for the shortest path while L2 returns the statistics for the path considering elevation
        If we are going from node "1" to node "2" : 
        total positive change in elevation : (max(0, elev("2") - elev("1"))
        total negative change in elevation : (max(0, elev("1") - elev("2"))
        If the start_location, end_location are outside the defined graph, L1 and L2 will be None.
        L2 will be None incase no route is found by our custom algorithms.
        """
        G = self.G
        self.x = x/100.0
        self.mode = mode
        self.start_node, self.end_node = None, None

        #self.best = [path, totalDist, totalElevGain, totalElevDrop]
        if mode == "maximize": 
            self.best = [[], 0.0, float('-inf'), float('-inf')]
        else:
            self.best = [[], 0.0, float('inf'), float('-inf')]

        #get shortest path
        self.start_node, d1 = ox.get_nearest_node(G, point=start_location, return_dist = True)
        self.end_node, d2   = ox.get_nearest_node(G, point=end_location, return_dist = True)

        # returns the shortest route from start to end based on distance
        self.shortest_route = nx.shortest_path(G, source=self.start_node, target=self.end_node, weight='length')
        
        # ox.get_route function returns list of edge length for above route
        self.shortest_dist  = sum(ox.get_route_edge_attributes(G, self.shortest_route, 'length'))
        
        print("dijkstra")
        self.all_dijkstra()

        shortest_route_latlong = [[G.nodes[route_node]['x'],G.nodes[route_node]['y']] for route_node in self.shortest_route] 
        
        shortestPathStats = [shortest_route_latlong, self.shortest_dist, \
                            self.computeElevs(self.shortest_route, "gain-only"), self.computeElevs(self.shortest_route, "drop-only")]

        # If dijkstra doesn't return a shortest path based on elevation requirements
        if (self.mode == "maximize" and self.best[2] == float('-inf')) or (self.mode == "minimize" and self.best[3] == float('-inf')):            
            return shortestPathStats, [[], 0.0, 0, 0]
        
        self.best[0] = [[G.nodes[route_node]['x'],G.nodes[route_node]['y']] for route_node in self.best[0]] 

        return shortestPathStats, self.best
