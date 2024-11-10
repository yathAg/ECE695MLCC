import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Read the CSV files with proper datetime parsing
pdu_path = Path('..') / 'Power_trace' / 'cella_pdu6_time_converted_hourly.csv'
ciso_path = Path('..') / 'CI_trace' / 'CISO.csv'

pdu_df = pd.read_csv(pdu_path, parse_dates=['hour'])
ciso_df = pd.read_csv(ciso_path, parse_dates=['datetime'])

# Merge the DataFrames on the datetime columns
merged_df = pd.merge(
    pdu_df,
    ciso_df,
    left_on='hour',
    right_on='datetime',
    how='inner',
    sort=True
)

# Compute the product of measured_power_util and carbon_intensity_actual
merged_df['product'] = merged_df['measured_power_util'] * merged_df['carbon_intensity_actual']

# Set the datetime as the index for plotting
merged_df.set_index('hour', inplace=True)

# Create the plot with a secondary y-axis
fig, ax1 = plt.subplots(figsize=(15, 7))

color1 = 'tab:blue'
ax1.set_xlabel('Time')
ax1.set_ylabel('Carbon Intensity Actual and Product', color=color1)
ax1.plot(merged_df.index, merged_df['carbon_intensity_actual'], label='Carbon Intensity Actual', color='orange')
ax1.plot(merged_df.index, merged_df['product'], label='Product', color='green')
ax1.tick_params(axis='y', labelcolor=color1)

# Create a second y-axis
ax2 = ax1.twinx()  
ax2.set_ylim(0.2, 3) 
color2 = 'tab:blue'
ax2.set_ylabel('Measured Power Util', color=color2)
ax2.plot(merged_df.index, merged_df['measured_power_util'], label='Measured Power Util', color=color2)
ax2.tick_params(axis='y', labelcolor=color2)

# Combine legends from both axes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

plt.title('Measured Power Util, Carbon Intensity Actual, and Their Product Over Time')
plt.tight_layout()

# Save the plot as a PNG image
plt.savefig('plot.png')
plt.close()