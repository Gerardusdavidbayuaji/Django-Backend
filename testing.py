import requests

geoserver_enpoint = "http://admin:geoserver@127.0.0.1:8080/geoserver"
workspace = "gsdb_simadu"

store = "test-store6"
data = f"C:/GD/1_Testing/upload_fews/backend/fews/repository/genangan_rob_jatim/genangan_rob_jatim.shp"
file_type = "shp"
store_type = "datastores" if file_type == 'shp' else "coveragestores"

url = f"{geoserver_enpoint}/rest/workspaces/{workspace}/{store_type}/{store}/external.{file_type}"

headers = {"Content-type": "text/plain"}
requests.put(url, data=data, headers=headers)