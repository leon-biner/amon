# Installation

The installation is via GitHub (for now):

```bash
pip install git+ssh://git@github.com/leon-biner/amon.git
```

> Note: This is a private repository.

Eventually, the package will be published on PyPI, and installation will simply be:

```bash
pip install amon
```

To verify the installation, run:

```bash
amon check
```

> Note: Some utility scripts (e.g., for generating starting points) are included for development purposes only and will be removed in the final release.

# Usage

The program can be run from anywhere using the `amon` command.

To view all available commands:

```bash
amon -h
```

To view the help menu for a specific subcommand, `run` for example:

```bash
amon run -h
```

The environment variable `AMON_HOME` can be used to navigate the internal package file structure.  
For example, to provide the starting point file `x1.txt`:

```bash
AMON_HOME/starting_pts/x1.txt
```


# Commands

## run

The `run` command is the central one, as it launches the blackbox. 

The full list of arguments and flags can be viewed using the help menu:
```bash
amon run -h
```

The first argument is either:
- A path to a **parameter file**, or
- An **instance number**, which refers to a pre-defined parameter file located in the [`amon/instances/`](amon/instances/) folder.

> Note: Details about writing parameter files are available in [`amon/blueprint.py`](amon/blueprint.py).

The second argument is the **point file** to evaluate.  
This file contains a single line of **space-separated values**, each corresponding to a specific optimization variable.

Let *n* be the number of wind turbines. The point file must contain exactly 5*n values, in the following order:

1. **2n values** for turbine positions:
   ```
   x_1 y_1 x_2 y_2 ... x_n y_n
   ```
2. **n values** for turbine types :
   ```
   t_1 t_2 ... t_n
   ```
	> Note: Types are indexed relative to those available in the parameter file, see the `instance-info` command to see an instance's parameter file details
3. **n values** for hub heights:
   ```
   h_1 h_2 ... h_n
   ```
4. **n values** for yaw angles:
   ```
   yaw_1 yaw_2 ... yaw_n
   ```

So, the full format is:

```text
x_1 y_1 x_2 y_2 ... x_n y_n t_1 ... t_n h_1 ... h_n yaw_1 ... yaw_n
```

**Example**: For a farm with 4 turbines and 2 available turbine models:

```text
x_1 y_1 x_2 y_2 x_3 y_3 x_4 y_4 t_1 t_2 t_3 t_4 h_1 h_2 h_3 h_4 yaw_1 yaw_2 yaw_3 yaw_4
```

Where:
- `x_n` = x-coordinate of turbine *n* 
- `y_n` = y-coordinate of turbine *n*  
- `t_n` = type index of turbine *n* 
- `h_n` = hub height of turbine *n*  
- `yaw_n` = yaw angle of turbine *n*

### Flags

```
-s SEED     : Set the random seed (random by default if not specified)
-r          : Send request to the local server instead of running directly (see the `serve` command)
--port PORT : Specify the port for the local server
--debug     : Show full error tracebacks for debugging
```

## show-windrose

The `show-windrose` command is used to display a specific wind data (from 1 to 4) in the form of a windrose.

The first and only argument is the id of the wind data.

### Flags
 
```
--save  : Save image (png) to specified path
--debug : Show full error messages
```

## show-zone

The `show-zone` command is used to display a specific zone (from 1 to 5).

The first and only argument is the id of the zone.

### Flags

```
--point        : Display turbine locations of specified point on top of zone
--save         : Save image (png) to specified path
--no-grid      : Turn off the grid
--scale-factor : Scale the size of the zone by a certain factor
--debug        : Show full error messages
```

## show-turbine

The `show-turbine` command displays the power/ct curve of a specific turbine (from 1 to 6), as well as its default height and its diameter.

The first and only argument is the id of the turbine.

### Flags

```
--save  : Save image (png) to specified path
--debug : Show full error messages
```

## show-elevation

The  `show-elevation` command is used to display the 3D elevation function (currently only 1 available).

The first and only argument is the id of the function.

### Flags
 
```
--limits : Set the domain over which to plot the function (4 arguments, x_low, y_low, x_high, y_high)
--save   : Save image (png) to specified path
--debug  : Show full error messages
```

## instance-info

The `instance-info` command is used to display details about an instance, such as the number of turbines, the available models, etc.

The first and only argument is the id of the instance.

### Flags

```
--debug : Show full error messages
```

## serve

The `serve` command is used to launch a local server that hosts a Python session.

Once the server is running, requests can be sent to it using the `-r` flag with the `amon run` command.  
This allows the client to repeatedly call the blackbox without reloading libraries or reinitializing objects, since the server's session remains active between calls.

To use the server, start it in a separate terminal:

```bash
amon serve
```

Then, call the blackbox with the `r` flag to send requests to the server:

```bash
amon run -r ...
```

> Note: HTTP POST requests will be logged in the server terminal.

### Flags

```
--port  PORT  : Set the port number (default: 8765)
--debug       : Show full error tracebacks
```


## shutdown

The `shutdown` command is used to shut the server down. This can also be done by killing the server's process.
A confirmation or error message is sent to indicate if the server has been properly shut down or not.

### Flags

```
--port  : Set a port number (default: 8765), matching the server's port
--debug : Show full error messages
```

## check

The `check` command is only used to verify if the output is consistent with other machines.

## File structure

The file structure is as follows:

```
amon/
├── src/
│   └── *.py
├── instances/
│   └── instance_n/
│       └── param_file.txt
├── data/
│   ├── elevation_functions/
│   │   └── elevation_function_n.py
│   ├── wind_data/
│   │   └── wind_data_n/
│   │       ├── wind_direction.csv
│   │       └── wind_speed.csv
│   ├── wind_turbines/
│   │   └── wind_turbine_n/
│   │       ├── properties.csv (name, diameter, hub_height)
│   │       └── powerct_curve.csv (windspeeds, power_values, ct_values)
│   └── zones/
│       └── zone_n/
│           ├── boundary_zone.shp
│           └── exclusion_zone.shp
├── starting_pts/
│   └── xn.txt
├── blueprint.py
```

README.md, .gitignore, and other files (at top level)

## More info

More details are available in [`amon/blueprint.py`](amon/blueprint.py)
