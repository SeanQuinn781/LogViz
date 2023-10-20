import requests
import time
import webbrowser

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

if __name__ == "__main__":
    ip_addresses = [
        "114.119.149.109",
        "89.178.129.86",
        "147.161.195.21",
        "198.235.24.2"
    ]

    for ip in ip_addresses:
        result = geolocate(ip)
        print('result is: ', result)
        # Check if result is a dictionary or an error string
        if isinstance(result, dict):
            for key, value in result.items():
                print(f"{key}: {value}")
        else:
            print(result)  # print the error message directly
        
        print('-' * 40)  # Print a separator line for readability
        
        # Open the IP in a web browser for manual verification
        # browser_url = f"https://geolocation-db.com/?ip={ip}"
        # browser_url = f"https://geolocation-db.com/jsonp/{ip_address}&position=true"
        # webbrowser.open(browser_url, new=2)  # 'new=2' ensures that a new browser tab/window is opened

        # Add a delay between requests and browser opening
        time.sleep(10)  # 10-second delay
