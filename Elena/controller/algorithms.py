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


    def shortest_path(self, start_location, end_location, x, mode = "maximize", log = True):
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
        list contains four items : [best route found, 
                                        total distance between the start and ending nodes of the best route, 
                                        total positive change in elevation,
                                        total negative change in elevation ]
        L1 returns the statistics for the shortest path
        If we are going from node "1" to node "2" : 
        total positive change in elevation : (max(0, elev("2") - elev("1"))
        total negative change in elevation : (max(0, elev("1") - elev("2"))
        """
        G = self.G
        self.x = x/100.0
        self.mode = mode
        self.start_node, self.end_node = None, None

        #get shortest path
        self.start_node, d1 = ox.get_nearest_node(G, point=start_location, return_dist = True)
        self.end_node, d2   = ox.get_nearest_node(G, point=end_location, return_dist = True)

        # returns the shortest route from start to end based on distance
        self.shortest_route = nx.shortest_path(G, source=self.start_node, target=self.end_node, weight='length')
        
        # ox.get_route function returns list of edge length for above route
        self.shortest_dist  = sum(ox.get_route_edge_attributes(G, self.shortest_route, 'length'))
        
        shortest_route_latlong = [[G.nodes[route_node]['x'],G.nodes[route_node]['y']] for route_node in self.shortest_route] 
        
        shortestPathStats = [shortest_route_latlong, self.shortest_dist, \
                            self.computeElevs(self.shortest_route, "gain-only"), self.computeElevs(self.shortest_route, "drop-only")]
         
        return shortestPathStats
