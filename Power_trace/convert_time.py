"""
This script updates the 'time' column in a CSV file to start from a specified date with 5-minute increments.
The script takes a CSV file as a command-line argument, processes it to replace the time values, 
and saves the result with "_time_converted" appended to the original file name.

Usage:
    python script_name.py <input_file>

Example:
    python script_name.py input_data.csv

Parameters:
    - input_file: str, the path to the input CSV file

The script assumes the following:
    - The 'time' column in the input file is in a numeric or timestamp format.
    - The output will be saved in the same directory as the input file with "_time_converted" appended to the filename.
"""

import pandas as pd
from datetime import datetime, timedelta
import os
import sys

def update_time_column(input_file, start_date_str='2019-05-01 00:00:00'):
    """
    Updates the 'time' column in a CSV file to start from a specified date with 5-minute increments.
    Saves the result with "_time_converted" appended to the original file name.
    
    Parameters:
    - input_file: str, the path to the input CSV file.
    - start_date_str: str, the starting date and time in 'YYYY-MM-DD HH:MM:SS' format.
    """
    
    # Load data from the CSV file
    df = pd.read_csv(input_file)
    
    # Parse the start date
    start_date = datetime.strptime(start_date_str, '%Y-%m-%d %H:%M:%S')
    
    # Generate new time values with increments of 5 minutes
    df['time'] = [start_date + timedelta(minutes=5 * i) for i in range(len(df))]
    
    # Format the time as 'YYYY-MM-DD H:MM:SS'
    df['time'] = df['time'].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    # Create output file name by appending "_time_converted" to the input file name
    base, ext = os.path.splitext(input_file)
    output_file = f"{base}_time_converted{ext}"
    
    # Save the updated DataFrame to a new CSV file
    df.to_csv(output_file, index=False)
    print(f"Updated file saved as {output_file}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python script_name.py <input_file>")
        sys.exit(1)

    input_file = sys.argv[1]
    update_time_column(input_file)
