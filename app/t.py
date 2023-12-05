#!flask/bin/python

# for file upload module
import os
import json as simplejson
import asyncio

from flask import (
    Flask,
    flash,
    request,
    render_template,
    redirect,
    url_for,
    send_from_directory,
)
from flask_bootstrap import Bootstrap

# updated 9-20-23 from werkzeug import secure_filename
from werkzeug.utils import secure_filename
from lib.upload_file import uploadfile

import json
from ip2geotools.databases.noncommercial import DbIpCity
import itertools
import re
import requests
from ip6Regex import ip6Regex
from os.path import join, dirname, realpath
from getStatusCode import getStatusCode
from allowedFile import allowedFileExtension, allowedFileType

import time
import os
import re
from ip2geotools.databases.noncommercial import DbIpCity
import requests
import json as simplejson



app = Flask(__name__)
app.config["SECRET_KEY"] = "hh_jxcdsfdsfcodf98)fxec]|"
app.config["UPLOAD_DIR"] = "static/data/"
app.config["ASSET_DIR"] = "static/mapAssets/"
app.config["CLEAN_DIR"] = "static/cleanData/"
app.config["HTML_DIR"] = "static/"


def rasterizeData(self, resLat=200, resLong=250):

    # Split map into resLat*resLong chunks
    # count visits to each, return "raster"
    # list with geolocation(x,y)/status/ip/os/full log lines
    print('in rasterizeData ')
    latStep, longStep = 180 / resLat, 360 / resLong
    # Build the rasterised coord. system
    gridX, gridY = [], []
    x = -180
    y = -90

    for i in range(resLong):
        gridX.append(x)
        x += longStep
    gridX.reverse()

    for i in range(resLat):
        gridY.append(y + i * latStep)
    gridY.reverse()

    gridItems = itertools.product(gridX, gridY)
    grid = {i: 0 for i in gridItems}
    print("HERE, the grid is made ")
    # assign each data point to its grid squares
    with open(self.analysis, "r") as json_file:
        data = json.load(json_file)
        print("assigning data point to its grid square")
        print('data is ', data)
        for point in data:
            print("point is: ", point)
            loc = DbIpCity.get(point['ip'], api_key='free')
            print('loc here is: ', loc)
            if loc is None:
                print('nothin')
                return
            else:
                print('got it, loc is : ', loc)
            # lat = loc["longitude"]
            # lon = loc["latitude"]

            
                print('lat, lon is ', loc.latitude, loc.longitude)
                print('gridX is: ', gridX)
                for x in gridX:
                    print('iterating latitutdes ')
                    if loc.latitude >= x:
                        coordX = x
                        break
                for y in gridY:
                    if loc.longitude >= y:
                        coordY = y
                        break
                grid[(coordX, coordY)] += 1
                print('no grid is: ', grid)

            # remove squares with 0 entries
            for key in list(grid.keys()):
                if grid[key] == 0:
                    del grid[key]

            # center squares
            raster = []
            # creating raster and information object
            for key, point in zip(grid, data):
                x = round(key[0] + longStep / 2, 5)
                y = round(key[1] + latStep / 2, 5)
                raster.append(
                    [
                        [x, y],
                        grid[key],
                        point["status"],
                        point["ip"],
                        point["OS"],
                        point["fullLine"],
                    ]
                )
            # note size of grid squares
            self.information["dx"] = round(longStep / 2, 5)
            self.information["dy"] = round(latStep / 2, 5)
            # generate responseJson
            with open(self.responseJson, "w") as json_dump:
                json.dump(
                    {"information": self.information, "raster": raster}, json_dump
                )

def geolocate(ip_address):
    try:
        url = f"https://geolocation-db.com/jsonp/{ip_address}&position=true"
        response = requests.get(url)
        # Clean the returned JSONP response to be a valid JSON
        json_response = response.text.split("(")[1].strip(")")
        data = eval(json_response)
        return {
            'IP': ip_address,
            'Country': data.get('country_name', "N/A"),
            'State': data.get('state', "N/A"),
            'City': data.get('city', "N/A"),
            'Latitude': data.get('latitude', "N/A"),
            'Longitude': data.get('longitude', "N/A")
        }
    except Exception as e:
        # return f"Error for IP {ip_address}: {e}"
        print(f"Error for IP {ip_address}: {e}")
        print('trying second API')
        loc = DbIpCity.get(ip_address, api_key='free')
        if loc is not None:
            # print('loc: ', loc)
            return {
                'IP': ip_address,
                'Country': loc.country,
                'State': loc.region,
                'City': loc.city,
                'Latitude': loc.latitude,
                'Longitude': loc.longitude
            }

class NginxLogParser:
    def __init__(self, logfile, index):
        self.data = {}  # Store IP and OS
        self.all_ips = {}
        # json for each log file with geolocation, os, status code
        self.clean_dir=app.config["CLEAN_DIR"],
        self.analysis = self.clean_dir + logfile + "-" + "analysis.json"
        self.raw_dir=app.config["UPLOAD_DIR"],
        self.asset_dir=app.config["ASSET_DIR"],
        self.html_dir=app.config["HTML_DIR"],

    def getIP(self, line):
        checkIp = line.split(" ")[0]
        rgx = re.compile("(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
        matchIp = rgx.search(checkIp)
        if matchIp:
            return matchIp.group(1)
        return None

    def getOS(self, line):
        try:
            context = line.split('(')[1].split(')')[0]
            rawOS = context.split(';')[1].strip().lower()
            if "win" in rawOS:
                return "Windows"
            elif "android" in rawOS:
                return "Android"
            elif "mac" in rawOS:
                if "ipad" in context or "iphone" in context:
                    return "iOS"
                return "Mac"
            elif "linux" in rawOS or "ubuntu" in rawOS:
                return "Linux"
            else:
                return "Other"
        except IndexError:
            return "Unknown"


    def parseFile(self, filePath):
        with open(filePath, 'r') as file:
            for line in file:
                ip = self.getIP(line)
                if ip and ip not in self.data:
                    os = self.getOS(line)
                    geolocation = geolocate(ip)
                    self.data[ip] = {'os': os, 'geolocation': geolocation}



# Print the current working directory
current_directory = os.getcwd()
# print("Current Directory:", current_directory)

# Name of the subdirectory you want to list (replace 'subdir' with its name)
subdir = "static/data/"

# Construct the full path to the subdirectory
subdir_path = os.path.join(current_directory, subdir)
logList = []

# Check if the subdirectory exists
if os.path.exists(subdir_path) and os.path.isdir(subdir_path):
    # print(f"Contents of {subdir}:")
    for item in os.listdir(subdir_path):
       if item.startswith('access'):
            logList.append(item)
            # print(f"  {item}")

print('Processing ', len(logList), ' log files')    
# Start processing
for index, log in enumerate(logList):
    print('index is: ', index)
    logPath = subdir_path + log
    # Example usage
    parser = NginxLogParser(logPath, index)
    parser.parseFile()


else:
    print(f"The directory {subdir} does not exist")


    

# Print parsed data
# for ip, data in parser.data.items():
    # print(f"IP: {ip}, OS: {data['os']}, Geolocation: {data['geolocation']}")
    # self.rasterizeData(),
    #self.createJs(loglist, index, logCount, allLogs)

# This will print each IP address with its OS and geolocation data



if __name__ == "__main__":
    app.debug = True
    if app.debug:
        print("DEBUGGING IS ON")
    else:
        print("DEBUGGING IS OFF")
    app.run(host="localhost")
