import os
import re
from ip2geotools.databases.noncommercial import DbIpCity
import requests


class NginxLogParser:
    def __init__(self):
        self.data = []  # Store IP and OS
        self.all_ips = {}

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
        #  print('filePath is, ', filePath)
        with open(filePath, 'r') as file:
            for line in file:
                ip = self.getIP(line)
                if ip and ip not in self.all_ips:
                    self.all_ips[ip] = ip
                    os = self.getOS(line)
                    self.data.append({'ip': ip, 'os' : os})

# Example usage
parser = NginxLogParser()

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
            logPath = subdir_path + item
            parser.parseFile(logPath)

else:
    print(f"The directory {subdir} does not exist")

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
    

for index, request in enumerate(parser.data):
    print(index, request)


print(parser.data)  # Prints the dictionary containing IP addresses and their corresponding OSes.




