## Installation

For now, the installation is via github, with pip install git+ssh://git@github.com/leon-biner/amon.git (private repo). Eventually, I will post it on PyPI, and the installation will simply be: pip install amon. To validate installation, type <amon check>

It is also good to mention that some files will not be there in the final version, such as the scripts used to write starting points for example.

## Usage

The program can be run from anywhere with the <amon> command. Add -h or --help after <amon> to see the different commands.
There are several commands, arguments, and flags. To see the help menu of a certain command, <run> for example, type <amon run -h>.

## Commands

# run

The <run> command is the central one, as it launches the balckbox. 
The arguments' details are available in the help menu of the run command : <amon run -h>.

The first argument is either a parameter file or an instance number. The instances are pre-made parameter files that can be investigated in the amon/instances/ folder. Details about writing parameter files are available in blueprint.py.
The second argument is the point file to evaluate. For now, this file is a single line of space-separated values, each corresponding to a specific variable. Let's denote by n the number of wind turbines. The first 2n values are the positions of the turbines in the form (x_1 y_1 x_2 y_2 ... x_n y_n). The next n values are the types of wind turbines, so the index of the wind turbine chosen within the available ones. For example, if the parameter file included turbines 1, 3, and 5, the corresponding types would be 0, 1, 2. After that comes the heights of each turbine, and then the yaw angles. There is a total of 5n values in a point.
**Point example**: Say there is a farm with 4 turbines to place and 2 models available. The point file would look like this:
x_1 y_1 x_2 y_2 x_3 y_3 x_4 y_4 t_1 t_2 t_3 t_4 h_1 h_2 h_3 h_4 yaw_1 yaw_2 yaw_3 yaw_4
where the x_n are the x values,
          y_n are the y values,
	  t_n are the types,
	  h_n are the heights,
	  and yaw_n are the yaw angles.

Flags
-----
There are multiple flags available:
	-s SEED     : Set the random seed, changes every call if not provided
	-r          : Send request to the local server instead of running directly (more on this in the **server** command section)
	--port PORT : Set the port used by the server
	--debug     : Shows full error messages

# show-windrose


