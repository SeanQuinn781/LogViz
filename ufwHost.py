"""
Simple python server that will execute commands sent from the mapService on the host.
"""
import time
import json
import subprocess
import requests
from urllib.parse import urlparse, parse_qs
from http.server import BaseHTTPRequestHandler, HTTPServer

HOST_NAME = "localhost"
PORT_NUMBER = 8080


class ufwHost(BaseHTTPRequestHandler):
    def do_HEAD(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("content-length"))
        field_data = self.rfile.read(length)
        print(field_data)
        self.send_response(200)
        self.end_headers()
        # TODO validate
        cmd = field_data
        print(cmd)
        p = subprocess.Popen(cmd, stdout=subprocess.PIPE, shell=True)
        p_status = p.wait()
        (output, err) = p.communicate()
        print(output)
        print("Command exit status/return code : ", p_status)
        self.wfile.write(cmd)
        return

    def respond(self, opts):
        response = self.handle_http(opts["status"], self.path)
        self.wfile.write(response)


if __name__ == "__main__":
    server_class = HTTPServer
    httpd = server_class((HOST_NAME, PORT_NUMBER), ufwHost)
    print(time.asctime(), "Server Starts - %s:%s" % (HOST_NAME, PORT_NUMBER))
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        pass
    httpd.server_close()
    print(time.asctime(), "Server Stops - %s:%s" % (HOST_NAME, PORT_NUMBER))
