import os
from flask import Flask, request, session, g, redirect, \
    url_for, abort, render_template, flash,jsonify
import requests
import json
import geopy
from geopy.geocoders import Nominatim
from Elena.control.algorithms import Algorithms
from Elena.abstraction.graph_model import Model



app = Flask(__name__, static_url_path = '', static_folder = "../presentation/static", template_folder = "../presentation/templates")
app.config.from_object(__name__)

app.config.from_envvar('APP_CONFIG_FILE', silent=True)

MAPBOX_ACCESS_KEY = 'pk.eyJ1Ijoia2V2aW5qb3NlcGgxOTk1IiwiYSI6ImNqbzUxc2kwaDAybm4zanRjdm9mbndqZW8ifQ.wdJv5gB84BWVy1dAoNN6ew'
# Mapbox driving direction API call
ROUTE_URL = "https://api.mapbox.com/directions/v5/mapbox/driving/{0}.json?access_token={1}&overview=full&geometries=geojson"

init = False
G, M, algorithms = None, None, None

def create_geojson(coordinates):
    geojson = {}
    geojson["properties"] = {}
    geojson["type"] = "Feature"
    geojson["geometry"] = {}
    geojson["geometry"]["type"] = "LineString"
    geojson["geometry"]["coordinates"] = coordinates

    return geojson

def create_data(start_location, end_location, x, min_max, log=True):
    """
    Prepares the data for the routes to be plotted. 
    """
    global init, G, M, algorithms

    locator = Nominatim(user_agent="myGeocoder")
    location = locator.reverse(start_location)
    locate = location.address.split(',')
    length = len(locate)

    start = locate[0] + ',' + locate[1] + ',' + locate[2] + ',' + locate[length-5] + ',' + \
            locate[length-3] + ', USA - ' + locate[length-2] 
    if log:
        print("Start: ",start)
    
    location = locator.reverse(end_location)
    locate = location.address.split(',')
    length = len(locate)

    end = locate[0] + ',' + locate[1] + ',' + locate[2] + ',' + locate[length-5] + ',' + \
            locate[length-3] + ', USA - ' + locate[length-2]
    if log:
        print("End: ",end)
    
    if log:
        print("Percent of Total path: ",x)
        print("Elevation: ",min_max)
    if not init:
        M = Model()
        G = M.get_graph(end_location)
        algorithms = Algorithms(G, x = x, elev_type = min_max)
        init = True
    
    shortestPath, elevPath = algorithms.shortest_path(start_location, end_location, x, elev_type = min_max, log = log)   
    
    if shortestPath is None and elevPath is None:
        data = {"elevation_route" : [] , "shortest_route" : []}        
        data["shortDist"] = 0
        data["gainShort"] = 0
        data["dropShort"] = 0
        data["elenavDist"]  = 0
        data["gainElenav"] = 0
        data["dropElenav"] = 0
        data["popup_flag"] = 0 
        return data
    data = {"elevation_route" : create_geojson(elevPath[0]), "shortest_route" : create_geojson(shortestPath[0])}
    data["shortDist"] = shortestPath[1]
    data["gainShort"] = shortestPath[2]
    data["dropShort"] = shortestPath[3]
    data["start"] = start
    data["end"] = end
    data["elenavDist"] = elevPath[1]
    data["gainElenav"] = elevPath[2]
    data["dropElenav"] = elevPath[3] 
    if len(elevPath[0])==0:
        data["popup_flag"] = 1
    else: 
        data["popup_flag"] = 2    
    return data
    
@app.route('/mapbox_gl_new')
def mapbox_gl_new():    
    """ 
    Renders the template html file
    """    

    return render_template(
        'mapbox_gl_new.html', 
        ACCESS_KEY=MAPBOX_ACCESS_KEY
    )


@app.route('/route',methods=['POST'])
def get_route():  
    """
    Prepares data required by the POST.
    Dumped as a JSON.
    """  
    data=request.get_json(force=True)
    route_data = create_data((data['start_location']['lat'],data['start_location']['lng']),(data['end_location']['lat'],data['end_location']['lng']),data['x'],data['min_max'])
    return json.dumps(route_data)
