# main.py
from amon.src.argparsing import create_parser
from amon.src.utils import DEFAULT_PORT, INSTANCES_PARAM_FILEPATHS, getInstanceInfo, getPath, simple_excepthook, check
import sys


def main():
    parser = create_parser(_runBB, _showWindrose, _showZone, _showTurbine, _showElevation, _instanceInfo, _check, _runServer, _shutdownServer)
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
        if args.instance_or_param_file > len(INSTANCES_PARAM_FILEPATHS):
            raise ValueError(f"\033[91mError\033[0m: Instance {args.instance_or_param_file} does not exist, choose from 1 to {len(INSTANCES_PARAM_FILEPATHS)}")
        args.instance_or_param_file = str(INSTANCES_PARAM_FILEPATHS[args.instance_or_param_file - 1])

    args.point = str(getPath(args.point))
    if args.r:
        from amon.src.client import runBBRequest
        result = [float(res) for res in runBBRequest(args).split()]
        print(f'{result[0]:.10f}', end=' ')
        for res in result[1:]:
            print(f'{res:.10f}', end=' ') 
        print()
    else:
        from amon.src.blackbox import runBB
        result = [float(res) for res in runBB(args).split()]
        print(f'{result[0]:.10f}', end=' ')
        for res in result[1:]:
            print(f'{res:.10f}', end=' ') 
        print()

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

def _instanceInfo(args):
    print(getInstanceInfo(args.instance_id))

def _check(args):
    print(check())

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