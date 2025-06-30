# client.py
import requests

def runBBRequest(args):
    try:
        response = requests.post(
            f"http://localhost:{args.port}/run",
            json={
                "instance_or_param_file" : args.instance_or_param_file,
                "point"                  : args.point,
                "s"                      : args.s
            }
        )
    except requests.exceptions.ConnectionError:
        raise requests.exceptions.ConnectionError(f"\033[91mError\033[0m: Could not connect to server at https://localhost:{args.port}")

    return response.text

def shutdownServer(args):
    try:
        response = requests.post(f"http://localhost:{args.port}/shutdown")
    except requests.exceptions.ConnectionError:
        raise ConnectionError(f"\033[91mError\033[0m: No server at port {args.port}")        
    if response.status_code == 200:
        print("\033[92mServer shut down successfully\033[0m")
    else:
        print("\033[91mServer is still up\033[0m")
