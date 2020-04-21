import osmnx as ox
import networkx as nx
import numpy as np
import pickle as p
import os
from Elena.abstraction.config import API

class Model:
    def __init__(self):
        print("Model Initialized")        
        self.GOOGLEAPIKEY=API["googleapikey"]        
        if os.path.exists("./graph.p"):
            self.G = p.load( open( "graph.p", "rb" ) )
            self.init = True
            print("Loaded Graph")
        else:
            self.init = False

    def get_graph_with_elevation(self, G):
        """
        Returns networkx graph G with eleveation data appended to each node and rise/fall grade to each edge.

        Params:
            bbox:tuple (n,s,e,w)
        Returns:
            G: networkx graph
        """
        # print(self.GOOGLEAPIKEY)
        G = ox.add_node_elevations(G, api_key=self.GOOGLEAPIKEY)        
        return G

    def distance_between_locs(self,lat1,lon1,lat2,lon2):
        """
        Return the distance between two locations given the lat/long's.
        """
        R=6371008.8 #radius of the earth
        
        lat1 = np.radians(lat1)
        lon1 = np.radians(lon1)
        lat2 = np.radians(lat2)
        lon2 = np.radians(lon2)

        dlon = lon2 - lon1
        dlat = lat2 - lat1

        a = np.sin(dlat / 2)**2 + np.cos(lat1) * np.cos(lat2) * np.sin(dlon / 2)**2
        c = 2 * np.arctan2(np.sqrt(a), np.sqrt(1 - a))

        distance = R * c
        return distance

    def add_dist_from_dest(self,G,end_location):
        """
        Adds distance from destination location to all the nodes in the graph
        Args:
        G : networkx multidigraph
        Returns
        G : networkx multidigraph
        """
        end_node=G.nodes[ox.get_nearest_node(G, point=end_location)]
        lat1=end_node["y"]
        lon1=end_node["x"]
        
        for node,data in G.nodes(data=True):
            lat2=G.nodes[node]['y']
            lon2=G.nodes[node]['x']
            distance=self.distance_between_locs(lat1,lon1,lat2,lon2)            
            data['dist_from_dest'] = distance
            
        return G

    def get_graph(self, end_location):
        """
        Return networkx graph with the elevation data added to the nodes. (If this class had already been called before it will load the cached
        graph to save time.) 
        """
        start_location = [42.384803, -72.529262]
        if not self.init:
            print("Loading Graph")
            self.G = ox.graph_from_point(start_location, distance=20000, network_type='walk')
            self.G = self.get_graph_with_elevation(self.G)                         
            p.dump( self.G, open( "graph.p", "wb" ) )
            self.init = True
            print("Saved Graph")
        self.G = self.add_dist_from_dest(self.G,end_location)
        return self.G

    
    
