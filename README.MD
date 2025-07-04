## Installation

For now, the installation is via github, with pip install git+ssh://git@github.com/leon-biner/amon.git (private repo). Eventually, I will post it on PyPI, and the installation will simply be: pip install amon. To validate installation, type <amon check>.

It is also good to mention that some files will not be there in the final version, such as the scripts used to write starting points for example.

## Usage

The program can be run from anywhere with the <amon> command. Add -h or --help after <amon> to see the different commands.
There are several commands, arguments, and flags. To see the help menu of a certain command, <run> for example, type <amon run -h>.

For filepaths, the variable <AMON_HOME> can be used to naviguate the amon package file structure. For example, to give amon the starting point x1.txt, you can write <AMON_HOME/starting_pts/x1.txt>

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
	-s SEED     : Set the random seed, changes every call if not provided
	-r          : Send request to the local server instead of running directly (more on this in the **server** command section)
	--port PORT : Set the port used by the server
	--debug     : Show full error messages

# show-windrose

The <show-windrose> command is used to display a specific wind data (from 1 to 4) in the form of a windrose.
The first and only argument is the id of the wind data.

Flags
-----
	--save  : Save image (png) to specified path
	--debug : Show full error messages

# show-zone

The <show-zone> command is used to display a specific zone (from 1 to 5).
The first and only argument is the id of the zone.

Flags
-----
	--point        : Display turbine locations of specified point on top of zone
	--save         : Save image (png) to specified path
	--no-grid      : Turn off the grid
	--scale-factor : Scale the size of the zone by a certain factor
	--debug        : Show full error messages

# show-turbine

The <show-turbine> command displays the power/ct curve of a specific turbine (from 1 to 6), as well as its default height and its diameter.
The first and only argument is the id of the turbine.

Flags
-----
	--save  : Save image (png) to specified path
	--debug : Show full error messages

# show-elevation

The <show-elevation> command is used to display the 3D elevation function (currently only 1 available).
The first and only argument is the id of the function.

Flags
-----
	--limits : Set the domain over which to plot the function (4 arguments, x_low, y_low, x_high, y_high)
	--save   : Save image (png) to specified path
	--debug  : Show full error messages

# instance-info

The <instance-info> command is used to display details about an instance, such as the number of turbines, the available models, etc.
The first and only argument is the id of the instance.

Flags
-----
	--debug : Show full error messages

# serve

The <serve> command is used to launch a local server. Once the server is up, it is possible to send requests to the server with the -r flag (see <run> command info) instead of opening a new session. The server will run the blackbox and send the result as a response.
This allows the blackbox to be called over and over again from a terminal without having to import libraries and construct certain objects again, as the server's session stays active while the client starts and stops his session every time. To use the server, simply start it in another terminal window with <amon serve>, and then call the blackbox with the <-r> flag. The http post requests can be seen in the server's terminal.

Flags
-----
	--port  : Set a port number (default is 8765)
	--debug : Show full error messages

# shutdown

The <shutdown> command is used to shut the server down. This can also be done by killing the server's process. It will confirm if the server has been properly shut down or not.

Flags
-----
	--port  : Set a port number (default is 8765), matching the server's port
	--debug : Show full error messages

# check

The <check> command is only used to verify if the output is consistent with other machines.

## File structure

The file structure is as follows:

|-- amon/
    |-- src/
        |-- *.py
    |-- instances/
        |-- instance_n/
            |-- param_file.txt
    |-- data/
        |-- elevation_functions/
            |-- elevation_function_n.py
        |-- wind_data/
            |-- wind_data_n/
                |-- wind_direction.csv
                |-- wind_speed.csv
        |-- wind_turbines/
            |-- wind_turbine_n/
                |-- properties.csv (name, diameter, hub_height)
                |-- powerct_curve.csv (windspeeds, power_values, ct_values)
        |-- zones/
            |-- zone_n/
                |-- boundary_zone.shp
                |-- exclusion_zone.shp
    |-- starting_pts/
	|-- xn.txt
    |-- blueprint.py
|-- README.MD, .gitignore, and other files

## More info

More info is available in the amon/blueprint.py file
