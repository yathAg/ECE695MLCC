import pandas as pd
import matplotlib.pyplot as plt
import sys
import os

# Get the file path from command-line arguments
if len(sys.argv) < 2:
    print("Usage: python script.py <input_csv_file>")
    sys.exit(1)

file_path = sys.argv[1]

# Check if file exists
if not os.path.isfile(file_path):
    print(f"File not found: {file_path}")
    sys.exit(1)

# Load data from CSV
df = pd.read_csv(file_path)

# Convert datetime column to pandas datetime format
df['datetime'] = pd.to_datetime(df['datetime'])

# Calculate ci average as the midpoint of lower bound and upper bound
df['ci average'] = (df['lower bound'] + df['upper bound']) / 2

# Plotting
plt.figure(figsize=(12, 6))
plt.plot(df['datetime'], df['actual'], label="Actual", color="blue")
plt.plot(df['datetime'], df['predicted'], label="Predicted", color="green")
plt.plot(df['datetime'], df['ci average'], label="CI Average", color="orange", linestyle="--")

plt.xlabel("Datetime")
plt.ylabel("Values")
plt.title("Actual vs Predicted vs CI Average")
plt.legend()
plt.xticks(rotation=45)
plt.tight_layout()

# Save the plot with the same name as the input file but with a .png extension
output_path = os.path.splitext(file_path)[0] + ".png"
plt.savefig(output_path, format='png', dpi=300)

print(f"Plot saved as {output_path}")
plt.show()
