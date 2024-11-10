import pandas as pd
import sys
import os

# Check if the input file name is provided
if len(sys.argv) < 2:
    print("Usage: python calculate_hourly_average.py <input_file.csv>")
    sys.exit(1)

input_file = sys.argv[1]

# Generate output file name by appending '_hourly' before the file extension
base_name, ext = os.path.splitext(input_file)
output_file = f"{base_name}_hourly{ext}"

# Read the CSV file
df = pd.read_csv(input_file)

# Parse the 'time' column as datetime
df['time'] = pd.to_datetime(df['time'])

# Floor the time to the nearest hour
df['hour'] = df['time'].dt.floor('H')

# Group by 'hour' and calculate the average 'measured_power_util'
hourly_avg = df.groupby('hour')['measured_power_util'].mean().reset_index()

# Save the result to a new CSV file
hourly_avg.to_csv(output_file, index=False)

print(f"Hourly average power data has been saved to {output_file}")
