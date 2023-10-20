import csv
import ipaddress

def load_geolite2_data(ip_blocks_filename, locations_filename):
    locations = {}
    ip_ranges = []
    
    # Load locations data
    with open(locations_filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            locations[row['geoname_id']] = row

    # Load IP blocks data
    with open(ip_blocks_filename, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            ip_ranges.append((ipaddress.ip_network(row['network']), row['geoname_id']))

    return ip_ranges, locations

def lookup_ip(ip, ip_ranges, locations):
    ip_addr = ipaddress.ip_address(ip)
    for network, geoname_id in ip_ranges:
        if ip_addr in network:
            location = locations.get(geoname_id, {})
            return {
                'IP Address': ip,
                'Country': location.get('country_name', "N/A"),
                'State': location.get('subdivision_1_name', "N/A"),
                'City': location.get('city_name', "N/A")
            }
    return f"No data for IP {ip}"

if __name__ == "__main__":
    ip_blocks_filename = 'geolite-data/GeoLite2-City-CSV_20231020/GeoLite2-City-Blocks-IPv4.csv'
    locations_filename = 'geolite-data/GeoLite2-City-CSV_20231020//GeoLite2-City-Locations-en.csv'
    ip_ranges, locations = load_geolite2_data(ip_blocks_filename, locations_filename)

    ip_addresses = [
        "114.119.149.109",
        "89.178.129.86",
        "147.161.195.21",
        "198.235.24.2"
    ]

    for ip in ip_addresses:
        result = lookup_ip(ip, ip_ranges, locations)
        for key, value in result.items():
            print(f"{key}: {value}")
        print('-' * 40)
