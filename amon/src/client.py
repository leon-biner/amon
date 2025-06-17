# client.py
import requests


def runBBRequest(args):
    try:
        response = requests.post(
            f"http://localhost:{args.port}/run",
            json={
                "instance_or_param_file" : args.instance_or_param_file,
                "point"                  : args.point
            }
        )
    except requests.exceptions.ConnectionError:
        return (f"\033[91mError\033[0m: Could not connect to server at https://localhost:{args.port}")

    return response.text

'''
def showWindroseRequest(args):
    try:
        response = requests.post(
            f"http://localhost:{args.port}/show-windrose",
            json={
                "wind_data_id" : args.wind_data_id,
                "save"         : args.save
            }
        )
    except requests.exceptions.ConnectionError:
        return (f"\033[91mError\033[0m: Could not connect to server at https://localhost:{args.port}")

    print(response)

def showTerrainRequest(args):
    try:
        response = requests.post(
            f"http://localhost:{args.port}/run",
            json={
                "zone_id"      : args.zone_id,
                "point"        : args.point,
                "save"         : args.save,
                "no_grid"      : args.no_grid,
                "scale_factor" : args.scale_factor
            }
        )
    except requests.exceptions.ConnectionError:
        return (f"\033[91mError\033[0m: Could not connect to server at https://localhost:{args.port}")

    print(response)
'''

def shutdownServer(args):
    try:
        requests.post(f"http://localhost:{args.port}/shutdown")
    except requests.exceptions.ConnectionError: # I am shutting down the server by killing its process, so connection breaks
        print("Server shut down successfully")
    else:
        print("Server has not shut down")
