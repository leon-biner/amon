# main.py
import time
from amon.src.argparsing import create_parser
from amon.src.utils import DEFAULT_PORT, INSTANCES_PARAM_FILEPATHS, getPath, simple_excepthook
import sys


def main():
    parser = create_parser(_runBB, _showWindrose, _showZone, _showTurbine, _showElevation, _runServer, _shutdownServer)
    args = parser.parse_args()
    if not args.debug:
        sys.excepthook = simple_excepthook
    args.func(args)
    

# Delay the imports to reduce unecessary import overhead
def _runBB(args):
    args.port = args.port if args.port is not None else DEFAULT_PORT
    try:
        args.instance_or_param_file = int(args.instance_or_param_file)
    except (ValueError, TypeError):
        args.instance_or_param_file = str(getPath(args.instance_or_param_file)) # we have to convert to string to send request
    else:
        args.instance_or_param_file = str(INSTANCES_PARAM_FILEPATHS[args.instance_or_param_file - 1])

    args.point = str(getPath(args.point))
    print("Running Blackbox ", end='')
    if args.s:
        print("from server...")
        from amon.src.client import runBBRequest
        print(runBBRequest(args))
    else:
        print("locally...")
        from amon.src.blackbox import runBB
        print(runBB(args))

def _showWindrose(args):
    if args.save:
        args.save = str(getPath(args.save))
    print("Showing windrose...")
    from amon.src.plot_functions import showWindrose
    showWindrose(args)

def _showZone(args):
    if args.point:
        args.point = str(getPath(args.point))
    if args.save:
        args.save = str(getPath(args.save))
    print("Showing zone...")
    from amon.src.plot_functions import showZone
    showZone(args)

def _showTurbine(args):
    from amon.src.plot_functions import showTurbine
    showTurbine(args)

def _showElevation(args):
    from amon.src.plot_functions import showElevation
    showElevation(args)

def _runServer(args):
    args.port = args.port if args.port is not None else DEFAULT_PORT
    from amon.src.server import runServer
    runServer(args)

def _shutdownServer(args):
    args.port = args.port if args.port is not None else DEFAULT_PORT
    from amon.src.client import shutdownServer
    shutdownServer(args)


if __name__ == "__main__":
    main()