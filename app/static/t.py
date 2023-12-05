import os
import re

class NginxLogParser:
    def __init__(self):
        self.data = {}  # Store IP and OS

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

    def parseDirectory(self, dirPath):
        print(self, dirPath)

        for root, dirs, files in os.walk(".", topdown=True):
            for name in files:
                print(os.path.join(root, name))
            for name in dirs:
                print(os.path.join(root, name))
            # for root, dirs, files in os.walk(dirPath):
            #     print('root dirs files are: ', root, dirs, files)
            # for file in files:
            #    self.parseFile(os.path.join(root, file))

    def parseFile(self, filePath):
        print('filePath is, ', filePath)
        with open(filePath, 'r') as file:
            for line in file:
                ip = self.getIP(line)
                print('ip is: ', ip)
                if ip:
                    os = self.getOS(line)
                    print('os is : ', os)
                    if ip not in self.data:
                        self.data[ip] = os

# Example usage
parser = NginxLogParser()


# Print the current working directory
current_directory = os.getcwd()
print("Current Directory:", current_directory)

# Name of the subdirectory you want to list (replace 'subdir' with its name)
subdir = "data"

# Construct the full path to the subdirectory
subdir_path = os.path.join(current_directory, subdir)
logList = []

# Check if the subdirectory exists
if os.path.exists(subdir_path) and os.path.isdir(subdir_path):
    print(f"Contents of {subdir}:")
    for item in os.listdir(subdir_path):
       if item.startswith('access'):
            logPath = subdir_path + item

            parser.parseFile(logPath)
           


print(parser.data)  # Prints the dictionary containing IP addresses and their corresponding OSes.

