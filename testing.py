import requests
import os

def upload_to_geoserver(file_path, file_type):
    geoserver_endpoint = "http://admin:geoserver@127.0.0.1:8080/geoserver"
    workspace = "gsdb_simadu"

    # Extract basename from file_path
    basename = os.path.basename(file_path)
    store = os.path.splitext(basename)[0]  # Use basename as store name
    store_type = "datastores" if file_type == 'shp' else "coveragestores"

    # URL of the file to be accessed by GeoServer
    file_url = f"file://{file_path.replace(os.sep, '/')}"
    
    # Construct URL for GeoServer REST API
    url = f"{geoserver_endpoint}/rest/workspaces/{workspace}/{store_type}/{store}/external.{file_type}"

    # Construct data payload for the PUT request
    data = file_url
    print("data to geoserver", data)

    # Make PUT request to GeoServer
    headers = {"Content-type": "text/plain"}
    try:
        response = requests.put(url, data=data, headers=headers)
        response.raise_for_status()  # Will raise an HTTPError for bad responses
    except requests.exceptions.RequestException as e:
        print(f"HTTP request failed: {e}")
        return False

    # Check if upload was successful
    if response.status_code in (201, 202):
        print(f"Successful upload to GeoServer: {file_path}")
        return True
    else:
        print(f"Failed upload to GeoServer: {file_path}, Status Code: {response.status_code}, Response: {response.text}")
        return False

if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='Upload file to GeoServer')
    parser.add_argument('file_path', type=str, help='Path to the file to be uploaded')
    parser.add_argument('file_type', type=str, choices=['shp', 'geotiff'], help='Type of the file (shp or geotiff)')
    
    args = parser.parse_args()
    
    success = upload_to_geoserver(args.file_path, args.file_type)
    if success:
        print("File uploaded successfully.")
    else:
        print("File upload failed.")
