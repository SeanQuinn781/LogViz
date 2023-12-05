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









    # self.getIPLocation()
    """ 
    L = await asyncio.gather(
        self.getIPLocation(),
        self.rasterizeData(),
        self.createJs(loglist, index, logCount, allLogs)
    )
    tasks = []
    tasks.append(asyncio.ensure_future(self.getIPLocation()))
    tasks.append(asyncio.ensure_future(self.rasterizeData()))
    tasks.append(
        asyncio.ensure_future(self.createJs(loglist, index, logCount, allLogs))
    )
    """



                """ 
            with open(self.analysis, "r") as json_file:
                data = json.load(json_file)
                # reader = geolite2.reader()
                result = []
                print('data is: ', data)
                for item in data:
                    ip = item["ip"]
                    # ip_info = reader.get(ip)
                    # ip_info = geolite2.lookup(ip)
                    print('first ip: ', ip)
                    print('whats a loc ')
                    loc = DbIpCity.get(ip, api_key='free')
                    print('this is a loc: ', loc)
                    ip = self.getIP(ip)
                    print("does ip exist here second one: ", ip)
                    loc = DbIpCity.get(ip, api_key='free')
                    try:
                        print('bla e')
                        entry = {}
                        entry["ip"] = self.getIP(item)
                        entry["OS"] = self.getOS(line)
                        entry["status"] = getStatusCode(line)
                        entry["fullLine"] = str(line)
                        entry["latitude"] = loc.latitude
                        entry["longitude"] = loc.longitude                
                        result.append(entry)
                        self.information["totalIPCount"] += 1
     

                    except Exception as e:
                        pass
                print("result is: ", result)


                if loc is not None:
                    print("ip_info is: ", loc)
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

            """