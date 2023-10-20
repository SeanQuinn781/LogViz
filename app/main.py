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
# updated 9-20-23 from geolite2 import geolite2
# import geoip2.webservice
# https://pythonhosted.org/python-geoip/
# from ip2geotools import DbIpCity
from ip2geotools.databases.noncommercial import DbIpCity
# from geoip import geolite2
import itertools
import re
import requests
from ip6Regex import ip6Regex
from os.path import join, dirname, realpath
from getStatusCode import getStatusCode
from allowedFile import allowedFileExtension, allowedFileType

import time

app = Flask(__name__)
app.config["SECRET_KEY"] = "hh_jxcdsfdsfcodf98)fxec]|"
app.config["UPLOAD_DIR"] = "static/data/"
app.config["ASSET_DIR"] = "static/mapAssets/"
app.config["CLEAN_DIR"] = "static/cleanData/"
app.config["HTML_DIR"] = "static/"

# app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

IGNORED_FILES = set([".gitignore"])
bootstrap = Bootstrap(app)


@app.route("/upload", methods=["GET", "POST"])
def upload():
    if request.method == "POST":
        files = request.files["file"]
        if files:
            filename = secure_filename(files.filename)
            mime_type = files.content_type
            validFileType = allowedFileType(mime_type)
            # if file extension is not log or a number (example: access.log.2)
            # or if file type,
            if not allowedFileExtension(files.filename) or validFileType == False:
                print("not a valid log file type")
                result = uploadfile(
                    name=filename,
                    type=mime_type,
                    size=0,
                    not_allowed_msg="File type not allowed in app.py validation",
                )

            else:
                uploaded_file_path = os.path.join(app.config["UPLOAD_DIR"], filename)
                files.save(uploaded_file_path)
                size = os.path.getsize(uploaded_file_path)
                result = uploadfile(name=filename, type=mime_type, size=size)

            return simplejson.dumps({"files": [result.get_file()]})

    # get all logs in ./data directory
    if request.method == "GET":
        files = [
            f
            for f in os.listdir(app.config["UPLOAD_DIR"])
            if os.path.isfile(os.path.join(app.config["UPLOAD_DIR"], f))
            and f not in IGNORED_FILES
        ]

        file_display = []

        for f in files:
            size = os.path.getsize(os.path.join(app.config["UPLOAD_DIR"], f))
            file_saved = uploadfile(name=f, size=size)
            file_display.append(file_saved.get_file())

        return simplejson.dumps({"files": file_display})

    return redirect(url_for("index"))


# serve static files
@app.route("/data/<string:filename>", methods=["GET"])
def get_file(filename):
    return send_from_directory(
        os.path.join(app.config["UPLOAD_DIR"]), filename=filename
    )


# once files are uploaded, requests can be made to /map to generate maps
@app.route("/map", methods=["GET"])
def logViz():
    class LogViz(object):
        # Class for analysing logs and generating interactive map
        def __init__(
            self,
            logfile,
            loglist,
            clean_dir=app.config["CLEAN_DIR"],
            raw_dir=app.config["UPLOAD_DIR"],
            asset_dir=app.config["ASSET_DIR"],
            html_dir=app.config["HTML_DIR"],
        ):
            super(LogViz, self).__init__()

            # dir with data, rw
            self.clean_dir = clean_dir

            # dir for src data
            self.raw_dir = raw_dir

            # dir with html, rw
            self.html_dir = html_dir
            self.html_file = html_dir + "map.html"

            # "location.js" loaded into the map in /static/index.html
            self.asset_dir = asset_dir

            # path to access.log
            self.access_file = raw_dir + logfile

            # arr to avoid duplicate ips
            self.all_ips = []

            # json for each log file with geolocation, os, status code
            self.analysis = self.clean_dir + logfile + "-" + "analysis.json"

            # contains general information and rasterised location data
            self.responseJson = self.clean_dir + logfile + "-" + "locations.json"

            # js file that loads the information and raster data from logs into map
            self.locationsJS = self.asset_dir + "locations.js"

            # list of all log files, containing the log name
            self.loglist = self.asset_dir + "loglist.js"
            self.ip_file = self.clean_dir + "ip.txt"

            # object with IPtotalIPCount number of IPs, also
            # sets the circumference of the data points on the map
            # based on the total # of ips. When there are many ips to render
            # on the Map the data points will have a smaller circumference
            self.information = {"totalIPCount": 0}

        def getIP(self, line):
            # print("in getIp")
            # ips in access.log should be in the first part of the line
            checkIp = line.split(" ")[0]
            # ip regex
            rgx = re.compile("(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})")
            matchIp = rgx.search(checkIp)




        
            def geolocate(ip_address):
                try:
                    url = f"https://geolocation-db.com/jsonp/{ip_address}&position=true"
                    response = requests.get(url)
                    # Clean the returned JSONP response to be a valid JSON
                    json_response = response.text.split("(")[1].strip(")")
                    data = eval(json_response)
                    return {
                        'IP Address': ip_address,
                        'Country': data.get('country_name', "N/A"),
                        'State': data.get('state', "N/A"),
                        'City': data.get('city', "N/A"),
                        'Latitude': data.get('latitude', "N/A"),
                        'Longitude': data.get('longitude', "N/A")
                    }
                except Exception as e:
                    return f"Error for IP {ip_address}: {e}"

            if matchIp is None:
                # if that match failed check the entire line for an IP match
                secondMatchIp = rgx.search(line)
                # if that match also failed, try ipv6
                if secondMatchIp is None:
                    matchIp6 = ip6Regex.search(line)
                    # print('ipv6 IP ', line)
            # make sure we have an ip
            if matchIp or secondMatchIp or matchIp6:
                # return the log line now an IP has been detected
                if checkIp not in self.all_ips: 
                    self.all_ips.append(checkIp)
                    with open(self.ip_file, "a") as record_ip:
                        record_ip.write(f'\n{checkIp}')


                        result = geolocate(checkIp)
                        print('result is result ', result)
                        # for key, value in result.items():
                            # print(f"{key}: {value}")


                else:
                    print('already recorded ip: ', checkIp)

                # return checkIp
            else:
                # TODO, handle this case instead of just printing the result
                print("Could not find an IP in this line")

        # isolate OS data from a log line
        def getContext(self, line):
            return line.rsplit('"')[5]

        # Gets the OS from a log file entry
        def getOS(self, line):
            context = self.getContext(line).rsplit("(")[1]
            rawOS = context.rsplit(";")[1].lower()
            if "win" in rawOS:
                return "Windows"
            elif "android" in rawOS:
                return "Android"
            elif "mac" in rawOS:
                if "ipad" or "iphone" in context:
                    return "iOS"
                else:
                    return "Mac"
            elif "linux" or "ubuntu" in rawOS:
                return "Linux"
            else:
                return "Other"
                # return rawOS

        def getIPData(self):
            print('in getIpData')

            print('self ip file is ', self.ip_file)
            print('analysis is ', self.analysis)
            with open(self.ip_file, "r") as data_file:
                with open(self.analysis, "w") as json_file:
                    result = []
                    for line in data_file:
                        # print("zz line is: ", line)
                        # ip = self.getIP(line)
                        # print("does ip exist here: ", ip)
                        # loc = DbIpCity.get(ip, api_key='free')
                        # print('db city ', DbIpCity)
                        try:
                            entry = {}
                            entry["ip"] = self.getIP(line)
                            entry["OS"] = self.getOS(line)
                            entry["status"] = getStatusCode(line)
                            entry["fullLine"] = str(line)
                            entry["latitude"] = loc.latitude
                            entry["longitude"] = loc.longitude                
                            result.append(entry)
                            self.information["totalIPCount"] += 1
                            print('full entry: ', entry)

                        except Exception as e:
                            pass
                    print("result is: ", result)

                    json.dump(result, json_file)
            print("Cleaned Data.")

        async def getIPLocation(self):
            # Scan ips for geolocation, add coordinates
            print("in getIPLocation ")
            self.getIPData()
            print('finished get ipdata, self.analsysis is ', self.analysis)
            with open(self.analysis, "r") as json_file:
                data = json.load(json_file)
                # reader = geolite2.reader()
                result = []
                print('data is: ', data)
                for item in data:
                    ip = item["ip"]
                    # ip_info = reader.get(ip)
                    # ip_info = geolite2.lookup(ip)
                    loc = DbIpCity.get(ip, api_key='free')
                    print("ip_info is: ", loc)
                    if ip_info is not None:
                        try:
                            item["latitude"] = loc.latitude
                            item["longitude"] = loc.longitude
                            result.append(item)
                        except Exception as e:
                            pass
                    else:
                        print('ip_info is none')

            with open(self.analysis, "w") as json_file:
                json.dump(result, json_file)

            print("Added locations")

        async def analyseLog(self, loglist, index, logCount, allLogs):
            L = await asyncio.gather(
                self.getIPLocation(),
                self.rasterizeData(),
                self.createJs(loglist, index, logCount, allLogs)
            )
            """
            tasks = []
            tasks.append(asyncio.ensure_future(self.getIPLocation()))
            tasks.append(asyncio.ensure_future(self.rasterizeData()))
            tasks.append(
                asyncio.ensure_future(self.createJs(loglist, index, logCount, allLogs))
            )
            """
            # print('tasks are: ', tasks)
            # await asyncio.gather(*tasks, return_exceptions=True)
            print("Rasterised Data")

        async def rasterizeData(self, resLat=200, resLong=250):

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
                    # loc = DbIpCity.get(point['ip'], api_key='free')
                    print('loc here is: ', loc)
                    # lat = loc["longitude"]
                    # lon = loc["latitude"]
                    print('lat, lon is ', loc.latitude, loc.longitude)
                    print('gridX is: ', gridX)
                    for x in gridX:
                        print('iterating latitutdes ')
                        if lon >= x:
                            coordX = x
                            break
                    for y in gridY:
                        if lat >= y:
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

        async def createJs(self, loglist, index, logCount, allLogs):
            # create js used to generate each map
            print('in createJs')
            with open(self.responseJson, "r") as response:
                loglistObj = "const LOGLIST = " + str(loglist)
                # add location data for each log file to []
                allLogs.append(json.load(response))
                print('allLogs is ', allLogs)
                # write js data for all log files to []
                if index == logCount:
                    dataString = "const LOCATIONS = " + str(allLogs)
                    with open(self.loglist, "w") as f:
                        f.write(loglistObj)
                    # write js data to locations.js
                    with open(self.locationsJS, "w") as f:
                        f.write(dataString)

                    print("Done!")
                else:
                    print('index doesnt equal log count, logcount is: ', logCount, 'index is: ', index)

    # create lists to build on with each log file that is processed
    files, accessLogs, allLogs = [], [], []
    # recursively build list of nginx/ denyhost logs
    for dirname, dirnames, filenames in os.walk(app.config["UPLOAD_DIR"]):
        for subdirname in dirnames:
            files.append(os.path.join(dirname, subdirname))

        for filename in filenames:

            if filename.startswith("access"):
                accessLogs.append(filename)

    logCount = len(accessLogs) - 1
    logMaps = []
    # used to test the execution time of map creation process while using async processing (as opposed to not using async)
    start = time.time()
    # For performance measurement, time.clock() is preferred 

    # uncommenting because its deprecated apparently:
    # https://stackoverflow.com/questions/58569361/attributeerror-module-time-has-no-attribute-clock-in-python-3-8
    # perfStart = time.clock()

    # set up a list of all the LogViz objects for processing later
    for index, accessLog in enumerate(accessLogs):
        logMaps.append(LogViz(accessLog, accessLogs))

    async def genMaps(logMaps):
        for logMap in logMaps:
            await logMap.analyseLog(accessLogs, index, logCount, allLogs)

    asyncio.run(genMaps(logMaps))

    # uncommenting because its deprecated apparently:
    end = time.time()
    print("time spent was ")
    print(end - start)
    print("maps have been generated")

    return render_template("map.html")


@app.route("/delete/<string:filename>", methods=["DELETE"])
def deleteFile(filename):

    print("File passed in was: ", filename)

    # function that actually deletes the files after they are gathered below
    def handleDelete(file, lastFile):

        # iterate through all files passed in

        if os.path.exists(file):
            try:
                print("Deleting file: ", file)

                os.remove(file)

                if lastFile:
                    return simplejson.dumps({filename: "True"})

            except:
                if lastFile:
                    return simplejson.dumps("False")

    # define files to be removed (these files are generated by each map)

    log_file = os.path.join(app.config["UPLOAD_DIR"], filename)
    analysis_json = os.path.join(app.config["CLEAN_DIR"], filename + "-analysis.json")
    locations_json = os.path.join(app.config["CLEAN_DIR"], filename + "-locations.json")
    ip_file = os.path.join(app.config["CLEAN_DIR"], "ip.txt")
    log_js = os.path.join(app.config["ASSET_DIR"], "loglist.js")
    locations_js = os.path.join(app.config["ASSET_DIR"], "locations.js")

    # call handleDelete on all the maps files
    # pass a flag to return on the last file TODO: clean this up
    isLastFile = False

    handleDelete(analysis_json, isLastFile)
    handleDelete(locations_json, isLastFile)
    handleDelete(ip_file, isLastFile)
    handleDelete(log_js, isLastFile)
    handleDelete(locations_js, isLastFile)

    isLastFile = True
    handleDelete(log_file, isLastFile)
    return render_template("index.html")


@app.route("/", methods=["GET", "POST"])
def index():
    return render_template("index.html")


@app.route("/map/<ip>", methods=["POST", "GET"])
def callHost(ip):
    print("blocking ", ip, " on the host machine..")

    """
    issue cmd from map_service to block the  IP on the host machine
    (ufw rules require sudo so you may need to enter your password once in the  servers terminal)
    """
    # TODO validate ip
    data = "sudo ufw deny in from " + ip
    try:
        response = requests.post(" http://localhost:8080", data=data)
    except Exception as e:
        return str(e)

    if response.status_code == 200:
        message = "Successfully executed " + data
        flash(data)
        return render_template("blockedIp.html", message=message)


if __name__ == "__main__":
    app.debug = True
    if app.debug:
        print("DEBUGGING IS ON")
    else:
        print("DEBUGGING IS OFF")
    app.run(host="localhost")
