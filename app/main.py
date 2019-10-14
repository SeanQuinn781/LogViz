#!flask/bin/python

# for file upload module
import os
import json as simplejson
from flask import Flask, flash, request, render_template, \
    redirect, url_for, send_from_directory, send_file
from flask_bootstrap import Bootstrap
from werkzeug import secure_filename
from lib.upload_file import uploadfile

import json
from geolite2 import geolite2
import itertools
import re
from ip6Regex import ip6Regex
from os.path import join, dirname, realpath
from getStatusCode import getStatusCode
from allowedFile import allowedFileExtension, allowedFileType

app = Flask(__name__)
app.config['SECRET_KEY'] = 'hh_jxcdsfdsfcodf98)fxec]|'
app.config['UPLOAD_DIR'] = 'static/data/'
app.config['ASSET_DIR'] = 'static/mapAssets/'
app.config['CLEAN_DIR'] = 'static/cleanData/'
app.config['HTML_DIR'] = 'static/'

# app.config['MAX_CONTENT_LENGTH'] = 100 * 1024 * 1024

IGNORED_FILES = set(['.gitignore'])
bootstrap = Bootstrap(app)

@app.route("/upload", methods=['GET', 'POST'])
def upload():
    if request.method == 'POST':
        files = request.files['file']
        print('IN UPLOAD')
        if files:
            filename = secure_filename(files.filename)
            mime_type = files.content_type
            validFileType = allowedFileType(mime_type)
            # if file extension is not log or a number (example: access.log.2)
            # or if file type, 
            if not allowedFileExtension(files.filename) or validFileType == False:
                print('not a valid log file type')
                result = uploadfile(name=filename, type=mime_type, size=0,
                                    not_allowed_msg="File type not allowed in app.py validation")

            else:
                uploaded_file_path = os.path.join(app.config['UPLOAD_DIR'], filename)
                files.save(uploaded_file_path)
                size = os.path.getsize(uploaded_file_path)
                result = uploadfile(name=filename, type=mime_type, size=size)

            return simplejson.dumps({"files": [result.get_file()]})

    # get all logs in ./data directory
    if request.method == 'GET':
        files = [f for f in os.listdir(app.config['UPLOAD_DIR']) if
                 os.path.isfile(os.path.join(app.config['UPLOAD_DIR'], f)) and f not in IGNORED_FILES]

        file_display = []

        for f in files:
            size = os.path.getsize(os.path.join(app.config['UPLOAD_DIR'], f))
            file_saved = uploadfile(name=f, size=size)
            file_display.append(file_saved.get_file())

        return simplejson.dumps({"files": file_display})

    return redirect(url_for('index'))

# serve static files
@app.route("/data/<string:filename>", methods=['GET'])
def get_file(filename):
    return send_from_directory(os.path.join(app.config['UPLOAD_DIR']), filename=filename)

# once files are uploaded, requests can be made to /map to generate maps
@app.route('/map', methods=['GET'])
def logViz():
    class LogViz(object):
        # Class for analysing logs and generating interactive map
        def __init__(
                self,
                logfile,
                loglist,
                clean_dir=app.config['CLEAN_DIR'],
                raw_dir=app.config['UPLOAD_DIR'],
                asset_dir=app.config['ASSET_DIR'],
                html_dir=app.config['HTML_DIR']):
            super(LogViz, self).__init__()

            # dir with data, rw
            self.clean_dir = clean_dir

            # dir for src data
            self.raw_dir = raw_dir

            # dir with html, rw
            self.html_dir = html_dir
            self.html_file = html_dir + 'map.html'

            # "location.js" loaded into the map in /static/index.html
            self.asset_dir = asset_dir

            # path to access.log
            self.access_file = raw_dir + logfile

            # json for each log file with geolocation, os, status code
            self.analysis = self.clean_dir + logfile + "-" + "analysis.json"

            # contains general information and rasterised location data
            self.responseJson = self.clean_dir + logfile + "-" + "locations.json"

            # js file that loads the information and raster data from logs into map
            self.locationsJS = self.asset_dir + "locations.js"

            # list of all log files, containing the log name
            self.loglist = self.asset_dir + "loglist.js"

            # object with IPtotalIPCount number of IPs, also
            # sets the circumference of the data points on the map
            # based on the total # of ips. When there are many ips to render 
            # on the Map the data points will have a smaller circumference 
            self.information = {"totalIPCount": 0}

        def getIP(self, line):
            # ips in access.log should be in the first part of the line
            checkIp = line.split(" ")[0]
            # ip regex
            rgx = re.compile('(\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3})')
            matchIp = rgx.search(checkIp)

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
                return checkIp
            else:
                # TODO, handle this case instead of just printing the result
                print('Could not find an IP in this line')

        def removeDuplicates(self):
            # Scans the log file for visits by the same ip and removes them.
            with open(self.access_file, "r") as f:
                # storing all already added IPs
                addedIPs = []
                # creating file that just stores the ips
                self.ip_file = self.clean_dir + "ip.txt"
                # file that stores the log lines without duplicate ips
                self.unique_data_file = self.clean_dir + "noDuplicatesLog.txt"
                with open(self.ip_file, "w") as dump:
                    with open(self.unique_data_file, "w") as clean:

                        # save IP unless its a duplicate found in the last 1000 IPs
                        for line in f:
                            IP = self.getIP(line)
                            if IP not in addedIPs[max(-len(addedIPs), -1000):] and IP is not None:
                                addedIPs.append(IP)
                                clean.write(line)
                            else:
                                pass

                    dump.write("\n".join(addedIPs))
            print("Removed Duplicates.")

        # isolate OS data from a log line
        def getContext(self, line):
            return (line.rsplit("\"")[5])

        # Gets the OS from a log file entry
        def getOS(self, line):
            context = self.getContext(line).rsplit("(")[1]
            rawOS = context.rsplit(";")[1].lower()
            if "win" in rawOS:
                return ("Windows")
            elif "android" in rawOS:
                return ("Android")
            elif "mac" in rawOS:
                if "ipad" or "iphone" in context:
                    return ("iOS")
                else:
                    return ("Mac")
            elif "linux" or "ubuntu" in rawOS:
                return ("Linux")
            else:
                return ("Other")
                # return rawOS

        def getIPData(self):
            # Removes duplicates and create file w. ip, OS and status code
            self.removeDuplicates()
            with open(self.unique_data_file, "r") as data_file:
                with open(self.analysis, "w") as json_file:
                    result = []
                    for line in data_file:
                        try:
                            entry = {}
                            entry["ip"] = self.getIP(line)
                            entry["OS"] = self.getOS(line)
                            entry["status"] = getStatusCode(line)
                            entry["fullLine"] = str(line)
                            result.append(entry)
                            self.information["totalIPCount"] += 1

                        except Exception as e:
                            pass

                    json.dump(result, json_file)
            print("Cleaned Data.")

        def getIPLocation(self):
            # Scan ips for geolocation, add coordinates
            self.getIPData()
            with open(self.analysis, "r") as json_file:
                data = json.load(json_file)
                reader = geolite2.reader()
                result = []
                for item in data:
                    ip = item["ip"]
                    ip_info = reader.get(ip)

                    if ip_info is not None:
                        try:
                            item["latitude"] = ip_info["location"]["latitude"]
                            item["longitude"] = ip_info["location"]["longitude"]
                            result.append(item)
                        except Exception as e:
                            pass

            with open(self.analysis, "w") as json_file:
                json.dump(result, json_file)

            print("Added locations")

        def analyseLog(self, loglist, index, logCount, allLogs):
            self.getIPLocation()
            self.rasterizeData()
            print("Rasterised Data")
            self.createJs(loglist, index, logCount, allLogs)

        def rasterizeData(self, resLat=200, resLong=250):

            # Split map into resLat*resLong chunks 
            # count visits to each, return "raster"
            # list with geolocation(x,y)/status/ip/os/full log line

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

            # assign each data point to its grid square
            with open(self.analysis, "r") as json_file:
                data = json.load(json_file)
                print("assigning data point to its grid square")
                for point in data:
                    lat, lon = point["latitude"], point["longitude"]
                    for x in gridX:
                        if lon >= x:
                            coordX = x
                            break
                    for y in gridY:
                        if lat >= y:
                            coordY = y
                            break
                    grid[(coordX, coordY)] += 1

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
                            point['status'],
                            point['ip'],
                            point['OS'],
                            point['fullLine']
                        ]
                    )
                # note size of grid squares
                self.information["dx"] = round(longStep / 2, 5)
                self.information["dy"] = round(latStep / 2, 5)
                # generate responseJson
                with open(self.responseJson, "w") as json_dump:
                    json.dump({"information": self.information,
                               "raster": raster}, json_dump)

        def createJs(self, loglist, index, logCount, allLogs):
            # create js used to generate each map
            with open(self.responseJson, "r") as response:
                loglistObj = "const LOGLIST = " + str(loglist)
                # add location data for each log file to []
                allLogs.append(json.load(response))
                # write js data for all log files to []
                if index == logCount:
                    dataString = "const LOCATIONS = " + str(allLogs)
                    with open(self.loglist, "w") as f:
                        f.write(loglistObj)
                    # write js data to locations.js
                    with open(self.locationsJS, "w") as f:
                        f.write(dataString)

                    print("Done!")

    # create lists to build on with each log file that is processed
    files, accessLogs, allLogs = [], [], []
    # recursively build list of nginx/ denyhost logs
    for dirname, dirnames, filenames in os.walk(app.config['UPLOAD_DIR']):
        for subdirname in dirnames:
            files.append(os.path.join(dirname, subdirname))

        for filename in filenames:

            if filename.startswith('access'):
                accessLogs.append(filename)

    logCount = len(accessLogs) - 1
    for index, accessLog in enumerate(accessLogs):
        logMap = LogViz(accessLog, accessLogs)
        logMap.analyseLog(accessLogs, index, logCount, allLogs)

        print('maps have been generated')
    # redirect user to the maps generated from logs
    return send_file('static/map.html')


@app.route("/delete/<string:filename>", methods=['DELETE'])
def delete(filename):
    # remove the log file
    log_file = os.path.join(app.config['UPLOAD_DIR'], filename)

    # remove the log file
    if os.path.exists(log_file):
        try:
            os.remove(log_file)

            return simplejson.dumps({filename: 'True'})
        except:
            return simplejson.dumps({filename: 'False'})


@app.route('/', methods=['GET', 'POST'])
def index():
    return render_template('index.html')

if __name__ == '__main__':
    app.debug = True
    if app.debug:
        print("DEBUGGING IS ON")
    else:
        print("DEBUGGING IS OFF")
    app.run(host='0.0.0.0')
