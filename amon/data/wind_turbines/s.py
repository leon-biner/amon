import csv

# filepath: /home/bineleon/Documents/AMON/amon/amon/data/wind_turbines/wind_turbine_3/filter_columns.py
# Specify the input and output file paths
input_file = "powerct_curve.csv"
output_file = "powerct_curve_2.csv"

# Specify the columns to keep (by header name)
new_columns = ["WindSpeed[m/s]", "Power[MW]", "Ct"]

# Read the input file and write the filtered output file
with open(input_file, 'r') as infile, open(output_file, 'w', newline='') as outfile:
    reader = csv.DictReader(infile)  # Read the CSV as a dictionary
    writer = csv.DictWriter(outfile, fieldnames=new_columns)  # Write only the specified columns

    # Write the header row for the output file
    writer.writeheader()

    for row in reader:
        # Create a filtered row with updated "Power [kW]" divided by 1000
        filtered_row = {
            "WindSpeed[m/s]": row["WindSpeed[m/s]"],
            "Power[MW]": float(row["Power[MW]"]) / 1000,  # Convert to MW
            "Ct": row["Ct"]
        }
        writer.writerow(filtered_row)
