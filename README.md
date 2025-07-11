# amon v0.2

# Installation

To install:

```bash
pip install amon-bb
```

> Note: pip needs to be installed

The application is installed in `$HOME/.local/bin`. This directory needs to be in your `$PATH`. To verify, run:

```bash
echo $PATH | tr ':' '\n' | grep "$HOME/.local/bin"
```

If you see an output looking like `/home/username/.local/bin`, it is already in your path, you can move on to the **Verification** step. If not, follow the steps below.

### Adding to $PATH globally

If using `bash`: 
```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.bashrc
```
If using `zsh`:

```bash
echo 'export PATH="$HOME/.local/bin:$PATH"' >> ~/.zshrc
```

### Adding to $PATH in current shell session

```bash
export PATH="$HOME/.local/bin:$PATH"
```

# Verification

To verify the installation:

```bash
amon check
```

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

## `instance-info`

The `instance-info` command is used to display details about an instance, such as the number of turbines, the available models, etc.

The first and only argument is the id of the instance.

### Flags

```
--debug : Show full error messages
```


## `run`

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

Let *n* be the number of wind turbines and *v* the number of optimization variables **for one turbine***. The point file must contain exactly *v* times *n* values. The order is defined in the parameter file, use the `instance-info` command and look for the `OPT_VARIABLES` line to see the order for a particular instance.

\* **Example**: if each turbine has its position and height controlled by an optimization variable, *v* would be **2**.  

The different of the point file are written as follows, with each index corresponding to a wind turbine:

1. **2n values** for turbine coordinates:
   ```
   x_1 y_1 x_2 y_2 ... x_n y_n
   ```
2. **n values** for turbine types :
   ```
   t_1 t_2 ... t_n
   ```
	> Note: Types are indexed starting from 0, and relative to those available in the parameter file Look for the `WIND_TURBINES` line of the `instance-info` command to see an instance's available models. If turbines **1**, **3**, and **5** are available, their respective types would be **0**, **1**, **2**.
3. **n values** for hub heights:
   ```
   h_1 h_2 ... h_n
   ```
4. **n values** for yaw angles:
   ```
   yaw_1 yaw_2 ... yaw_n
   ```


**Example**: Consider a farm with 4 turbines and and 2 available turbine models. 
The `instance-info` command or the parameter file shows this line: `OPT_VARIABLES COORDS, HEIGHT, TYPE`. The point file would be:

```text
x_1 y_1 x_2 y_2 x_3 y_3 x_4 y_4 h_1 h_2 h_3 h_4 t_1 t_2 t_3 t_4 
```

### Flags

```
-s SEED     : Set the random seed (random by default if not specified)
-r          : Send request to the local server instead of running directly (see the serve command)
-f FIDELITY : Set the fidelity (between 0 and 1)
--port PORT : Specify the port for the local server
--debug     : Show full error tracebacks for debugging
```

### Output

The output is set by the BLACKBOX_OUTPUT field of the parameter file. It can be seen for each instance with the `instance-info`command.

> **Example**: The parameter file has the line ```BLACKBOX_OUTPUT OBJ, SPACING, HEIGHT``` and the blackbox outputted ```100 5 -40```
   -> The objective function's value is **100**, the spacing constraint's is **5**, and the height constraint's is **-40**.

### Command example

```bash
amon run 1 AMON_HOME/starting_pts/x1.txt -s 3 -f 0.5
```

## `show-windrose`

The `show-windrose` command is used to display a specific wind data (from 1 to 4) in the form of a windrose.

The first and only argument is the id of the wind data.

### Flags
 
```
--save  : Save image (png) to specified path
--debug : Show full error messages
```

### Command example

```bash
amon show-windrose 1 --save path/to/file.png
```

## `show-zone`

The `show-zone` command is used to display a specific zone (from 1 to 5).

The first and only argument is the id of the zone.

### Flags

```
--point*       : Display turbine locations of specified point on top of zone
--save         : Save image (png) to specified path
--no-grid      : Turn off the grid
--scale-factor : Scale the size of the zone by a certain factor
--debug        : Show full error messages
```

\* The --point flag takes in 2 arguments: the path to the point file, and then number of turbines (in this order). The point file **must start with the coordinates**.

### Command example

```bash
amon show-zone 1 --save path/to/file.png --point AMON_HOME/starting_pts/x1.txt 30 --scale-factor 0.2
```

## `show-turbine`

The `show-turbine` command displays the power/ct curve of a specific turbine (from 1 to 6), as well as its default height and its diameter.

The first and only argument is the id of the turbine.

### Flags

```
--save  : Save image (png) to specified path
--debug : Show full error messages
```

### Command example

```bash
amon show-turbine 1 --save path/to/file.png
```

## `show-elevation`

The  `show-elevation` command is used to display the 3D elevation function (currently only 1 available).

The first and only argument is the id of the function.

### Flags
 
```
--limits : Set the domain over which to plot the function (4 arguments, x_low, y_low, x_high, y_high)
--save   : Save image (png) to specified path
--debug  : Show full error messages
```

### Command example

```bash
amon show-elevation 1 --save path/to/file.png --limits -100 -100 100 100
```

## `serve`

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

### Command example

```bash
amon serve --port 1234
```

Then with run:

```bash
amon run 1 AMON_HOME/starting_pts/x1.txt -r --port 1234
```

## `shutdown`

The `shutdown` command is used to shut the server down. This can also be done by killing the server's process.
A confirmation or error message is sent to indicate if the server has been properly shut down or not.

### Flags

```
--port  : Set a port number (default: 8765), matching the server's port
--debug : Show full error messages
```

### Command example

```bash
amon shutdown --port 1234
```

## `check`

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
