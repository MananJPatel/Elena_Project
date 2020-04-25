import sys
sys.path.insert(1, sys.path[0][:-5])
import osmnx as ox
import networkx as nx
from Elena.control.settings import *
from Elena.control.algorithms import *
from Elena.control.server import create_geojson, create_data
from Elena.abstraction.graph_model import *
import pickle as p
import geopy
from geopy.geocoders import Nominatim

def return_on_failure(value = ""):
    def decorate(f):
        def applicator(*args, **kwargs):
            try:
                f(*args,**kwargs)
                print("====>Passed " + u"\u2713\n")
            except Exception as e:
                print(e)
                print("====>Failed " + u"\u2717\n")
        return applicator
    return decorate

#get_graph
@return_on_failure("")
def test_get_graph(end):
    model = Model()
    G = model.get_graph(end)
    assert isinstance(G, nx.classes.multidigraph.MultiDiGraph)

# Create Geojson
@return_on_failure("")
def test_create_geojson(location):
    json = create_geojson(location)
    assert isinstance(json, dict)
    assert all(k in ["properties", "type", "geometry"] for k in json.keys())

# Create Data
@return_on_failure("")
def test_create_data(start, end, x = 0, min_max = "maximize"):
    d = create_data(start, end, x, min_max, log=False)
    locator = Nominatim(user_agent="myGeocoder")
    location = locator.reverse(start)
    locate = location.address.split(',')
    length = len(locate)

    start_loc = locate[0] + ',' + locate[1] + ',' + locate[2] + ',' + locate[length-5] + ',' + \
            locate[length-3] + ', USA - ' + locate[length-2]

    location = locator.reverse(end)
    locate = location.address.split(',')
    length = len(locate)

    end_loc = locate[0] + ',' + locate[1] + ',' + locate[2] + ',' + locate[length-5] + ',' + \
            locate[length-3] + ', USA - ' + locate[length-2]

    assert isinstance(d, dict)
    assert start_loc == d["start"]
    assert end_loc == d["end"]


# Get Cost function
@return_on_failure("")
def test_get_cost(A, n1 = 0, n2 = 1):
    
    c = A.get_cost(0, 1, cost_type = "normal")
    assert isinstance(c, float)
    assert c == 3.0
    
    c = A.get_cost(0, 3, cost_type = "elevation_difference")
    assert isinstance(c, float)
    assert c == 1.0

    c = A.get_cost(5, 4, cost_type = "elevation_difference")
    assert isinstance(c, float)
    assert c == -2.0
    
    c = A.get_cost(1, 4, cost_type= "elevation_gain")
    assert isinstance(c, float)
    assert c == 1.0

    c = A.get_cost(4, 1, cost_type = "elevation_gain")
    assert isinstance(c, float)
    assert c == 0.0
    
    c = A.get_cost(6, 2, cost_type = "elevation_drop")
    assert isinstance(c, float)
    assert c == 4.0
    
    c = A.get_cost(2, 6, cost_type = "elevation_drop")
    assert isinstance(c, float)
    assert c == 0.0

    c = A.get_cost(2, 6, cost_type = "abs")
    assert isinstance(c, float)
    assert c == 4.0

    c = A.get_cost(6, 2, cost_type = "abs")
    assert isinstance(c, float)
    assert c == 4.0

# Get Route
@return_on_failure("")
def test_get_route(A):
    c = A.get_route({0 : 1, 1 : 2, 2 : -1}, 0)
    assert isinstance(c, list)
    assert c == [2, 1, 0]


# Compute Elevations
@return_on_failure("")
def test_getElevation(A):
    route = [0, 6, 2]
    c, p = A.getElevation(route, cost_type = "both", isPiecewise = True)
    assert isinstance(c, float)
    assert isinstance(p, list)
    assert c == 0.0
    assert p == [4.0, -4.0]

    c = A.getElevation(route, cost_type = "both")
    assert isinstance(c, float)
    assert c == 0.0

    c, p = A.getElevation(route, cost_type = "elevation_gain", isPiecewise = True)
    assert isinstance(c, float)
    assert isinstance(p, list)
    assert c == 4.0
    assert p == [4.0, 0.0]

    c, p = A.getElevation(route, cost_type = "elevation_drop", isPiecewise = True)
    assert isinstance(c, float)
    assert isinstance(p, list)
    assert c == 4.0
    assert p == [0.0, 4.0]

    c, p = A.getElevation(route, cost_type = "normal", isPiecewise = True)
    assert isinstance(c, float)
    assert isinstance(p, list)
    assert c == 10.0
    assert p == [5.0, 5.0]


# Shortest Path algo
@return_on_failure("")
def test_shortest_path():
    
    #TESTING ALGO CORRECTNESS
    x = 100.0 #in percentage
    
    start_location, end_location = (42.3762, -72.5148), (42.3948, -72.5266)

    model = Model()
    G = model.get_graph(end_location)

    A = Algorithms(G, x = 100.0)

    sPath, elenavPath = A.shortest_path(start_location, end_location, x, elev_type = "maximize", log = False)
    assert elenavPath[1] <= (1 + x/100.0)*sPath[1]
    assert elenavPath[2] >= sPath[2]

    start_location, end_location = (42.3762, -72.5148), (42.3948, -72.5266)
    sPath, elenavPath = A.shortest_path(start_location, end_location, x, elev_type = "minimize", log = False)
    assert elenavPath[1] <= (1 + x/100.0)*sPath[1]
    assert elenavPath[2] <= sPath[2]

if __name__ == "__main__":
    start, end = (42.373222, -72.519852), (42.375544, -72.524210)
    
    G = nx.Graph()
    # Create toy graph with nodes 0-7
    [G.add_node(i, elevation = 0.0) for i in range(7)]
    edgeList = [(0,1,3.0), (1,2,3.0), (0,3,1.414), (3,4,4.0), (4,2,1.313), (0,5,4.24), (5,2,4.24), (0,6,5.0), (6,2,5.0)]
    G.add_weighted_edges_from(edgeList)
    elev = [0.0, 0.0, 0.0, 1.0, 1.0, 3.0, 4.0]

    # Add elevation data to graph
    for i, e in enumerate(elev):
        G.nodes[i]["elevation"] = e
    
    A = Algorithms(G, x = 0.0)

    # Testing Graph Model
    print("====>Testing get_graph")
    test_get_graph(end)

    # Testing server code
    print("====>Testing create_geojson")
    test_create_geojson(start)
    print("====>Testing create_data")
    test_create_data(start, end)
    
    # Testing algorithms code
    print("====>Testing get_cost")
    test_get_cost(A)
    print("====>Testing get_route")
    test_get_route(A)
    print("====>Testing getElevation")
    test_getElevation(A)
    print("====>Testing get_shortest_path")
    test_shortest_path()