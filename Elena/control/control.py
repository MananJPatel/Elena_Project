import os
import requests
import geopy
from flask import Flask, jsonify, session, g, request, url_for, flash, redirect,abort,render_template
from geopy.geocoders import Nominatim
import json
from Elena.abstraction.abstraction import Graph_Abstraction
from Elena.control.algorithms import Algorithms
from Elena.control.settings import *


app = Flask(__name__, static_url_path = '', static_folder = "../presentation/static", template_folder = "../presentation/templates")
app.config.from_object(__name__)

app.config.from_envvar('APP_CONFIG_FILE', silent=True)

MAPBOX_ACCESS_KEY = MAPBOX_KEY

init = False
G, M, algorithms = None, None, None

def get_geojson(coordinates):
    geojson = {}
    geojson["properties"] = {}
    geojson["type"] = "Feature"
    geojson["geometry"] = {}
    geojson["geometry"]["type"] = "LineString"
    geojson["geometry"]["coordinates"] = coordinates

    return geojson

def get_data(startpt, endpt, x, min_max, log=True):
    # gets data for plotting the routes. 
    global init, G, M, algorithms

    locator = Nominatim(user_agent="myGeocoder")
    location = locator.reverse(startpt)
    locate = location.address.split(',')
    
    len_location = len(locate)

    start = locate[0] + ',' + locate[1] + ',' + locate[2] + ',' + locate[len_location-5] + ',' + locate[len_location-3] + ', USA - ' + locate[len_location-2] 
    if log:
        print("Start: ",start)
    
    location = locator.reverse(endpt)
    locate = location.address.split(',')
    
    len_location = len(locate)

    end = locate[0] + ',' + locate[1] + ',' + locate[2] + ',' + locate[len_location-5] + ',' + locate[len_location-3] + ', USA - ' + locate[len_location-2]
    if log:
        print("End: ",end)
    
    if log:
        print("Percent of Total path: ",x)
        print("Elevation: ",min_max)
    if not init:
        abstract = Graph_Abstraction()
        G = abstract.get_graph(endpt)
        algorithms = Algorithms(G, x = x, elev_type = min_max)
        init = True
    
    shortestPath, elevPath = algorithms.get_shortest_path(startpt, endpt, x, elev_type = min_max, log = log)   
    
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
    data = {"elevation_route" : get_geojson(elevPath[0]), "shortest_route" : get_geojson(shortestPath[0])}
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
    
@app.route('/presentation')
def mapbox_gl_new():    

    return render_template(
        'presentation.html', 
        ACCESS_KEY=MAPBOX_ACCESS_KEY
    )

@app.route('/route',methods=['POST'])
def get_route():  
    data=request.get_json(force=True)
    route_data = get_data((data['start_location']['lat'],data['start_location']['lng']),(data['end_location']['lat'],data['end_location']['lng']),data['x'],data['min_max'])
    return json.dumps(route_data)
