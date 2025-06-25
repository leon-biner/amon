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
        raise requests.exceptions.ConnectionError(f"\033[91mError\033[0m: Could not connect to server at https://localhost:{args.port}")

    return response.text

def shutdownServer(args):
    try:
        requests.post(f"http://localhost:{args.port}/shutdown")
    except requests.exceptions.ConnectionError: # I am shutting down the server by killing its process, so connection breaks
        print("\033[92mServer shut down successfully\033[0m")
    else:
        print("\033[91mServer is still up\033[0m")
