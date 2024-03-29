LOGVIZ
===================

## Description
View the geolocation, status code, operating system and full request of IP addresses visiting visiting NGINX using tooltips on an SVG map

- Upload and processes multiple Nginx Log files and generate multiple maps at a time

- Backend: Flask for routing, processing logs, and python geoip2/maxmindDB for geolocation

- Frontend: React for UI, d3 for generating svg maps

- There is a separate repo for running LogViz in seperate flask containers, one for the uploading service and one for the map generation service: https://www.github.com/seanquinn781/LogViz-Docker

![](logviz.gif)

## Installation

LogViz can be installed and ran a few different ways, using docker, using docker-compose, by running the flask app with Python, or with gunicorn as a systemd service (see gunicorn_config for instructions)

# Python3 installation

1. Install python3 venv

```
sudo apt-get install python3-venv
```

2. Create virtual enviroment

```
cd LogViz
python3 -m venv venv
```

3. Activate virtual environment:
```
source venv/bin/activate
```

4. Install python requirements in the environment:  
```
pip3 install -r requirements.txt --user
```

5. Run the app

in dev mode with flask:

```
cd app && python3 main.py
```

Go to http://127.0.0.1:5000


Usage
==========================

1. Upload Log Files: Use the testing logs found in the test-logs directory, or Download Nginx access Log Files from your web server and unzip the files.

2. Upload multiple nginx log files to uploader at http://127.0.0.1:5000

3. click 'GENERATE MAP' and you will be routed to your maps

4. For more information about users OS, IP, request type etc, hover over datapoints on the SVG map

5. To switch to a different log file / map use the "Log Buttons" on the right side of the Map UI

To optionally deploy as a Gunicorn/ Systemd service See documentation and scripts in /app/gunicorn_config



If you run into errors uploading the files make sure you are in /app before running python3 main.py

## Blocking IPs from the map service on your host machine

1. Start the app and the python web server ufwHost.py:
python3 ufwHost.py
cd app && python3 main.py

3. Go to http://127.0.0.1:5000, upload your log files. Click generate map, hover over the request tooltip and click 'UFW block ip'

4. You will need to run sudo once in the web server terminal to execute the ufw rule



