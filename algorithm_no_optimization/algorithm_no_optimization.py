import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Define paths to the updated CSV files
power_trace_path = Path('..') / 'data_powerTrace' / 'cella_pdu6_converted.csv'
ci_data_path = Path('..') / 'data_SPC24' / 'SPCI-CISO' / 'CISO_direct_24hr_CI_forecasts_spci__alpha_0.1.csv'

# Read the CSV files with datetime parsing
power_trace_df = pd.read_csv(power_trace_path, parse_dates=['hour'])
ci_data_df = pd.read_csv(ci_data_path, parse_dates=['datetime'])

# Rename the 'actual' column in ci_data_df for clarity
ci_data_df.rename(columns={'actual': 'carbon_intensity_actual'}, inplace=True)

# Merge the DataFrames on the datetime columns
merged_df = pd.merge(
    power_trace_df,
    ci_data_df[['datetime', 'carbon_intensity_actual']],  # Select only required columns
    left_on='hour',
    right_on='datetime',
    how='inner',
    sort=True
)

# Compute the product of measured_power_util and carbon_intensity_actual
merged_df['product'] = merged_df['measured_power_util'] * merged_df['carbon_intensity_actual']

# Set the datetime as the index for plotting
merged_df.set_index('hour', inplace=True)

# Plotting the product and other values
fig, ax1 = plt.subplots(figsize=(15, 7))

ax1.set_xlabel('Time')
ax1.set_ylabel('Actual Carbon Intensity and Carbon emissions')
ax1.plot(merged_df.index, merged_df['carbon_intensity_actual'], label='Actual Carbon Intensity', color='orange')
ax1.plot(merged_df.index, merged_df['product'], label='Carbon emission', color='green')
ax1.tick_params(axis='y')

# Create a second y-axis for measured power utilization
ax2 = ax1.twinx()
ax2.set_ylim(0.2, 3) 
ax2.set_ylabel('Measured Power Utilization')
ax2.plot(merged_df.index, merged_df['measured_power_util'], label='Measured Power Utilization', color='blue')
ax2.tick_params(axis='y')

# Combine legends from both axes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

plt.title('Measured Power Utilization, Actual Carbon Intensity , and Carbon Emissions')
plt.tight_layout()

# Save the plot as a PNG image
plt.savefig('plot.png')
plt.close()
