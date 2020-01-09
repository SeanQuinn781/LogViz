def getStatusCode(line):
    splitLogLine = line.split('"', 2)[:3]
    statusCodeLine = splitLogLine[2].strip()
    statusCode = statusCodeLine[:3]
    return statusCode
