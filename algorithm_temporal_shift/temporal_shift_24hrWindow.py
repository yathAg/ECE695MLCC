import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Read the CSV files with proper datetime parsing
ciso_name = 'ISNE'  # Define the name of the CISO dataset
power_trace_path = Path('..') / 'data_powerTrace' / 'cella_pdu6_converted.csv'
ci_data_path = Path('..') / 'data_SPC24' / f'SPCI-{ciso_name}' / f'{ciso_name}_direct_24hr_CI_forecasts_spci__alpha_0.1.csv'

power_trace_df = pd.read_csv(power_trace_path, parse_dates=['hour'])
ci_data = pd.read_csv(ci_data_path, parse_dates=['datetime'])

# Rename the 'hour' column to 'datetime' for consistency
power_trace_df.rename(columns={'hour': 'datetime'}, inplace=True)

# Merge the two DataFrames on 'datetime'
merged_df = pd.merge(power_trace_df, ci_data, on='datetime')

# Total number of data points
num_rows = len(merged_df)

# Initialize lists to store results
shift_windows = list(range(0, 25))  # From 0 to 24 inclusive
total_carbon_emissions_list = []
peak_power_utilization_list = []

for shift_window in shift_windows:
    # Create a copy of the merged DataFrame to avoid modifying the original data
    merged_df_copy = merged_df.copy()
    
    if shift_window == 0:
        # No optimization; use original measured power utilization
        merged_df_copy['shifted_power_util'] = merged_df_copy['measured_power_util']
    else:
        # Initialize shifted_power_util to zeros
        merged_df_copy['shifted_power_util'] = 0.0

        # Iterate over each time point
        for i in range(num_rows):
            # Determine the window of future hours to consider
            end_idx = min(i + shift_window + 1, num_rows)  # +1 to include the current time
            forecast_window = merged_df_copy.iloc[i:end_idx]

            # Find the index with the minimum forecasted carbon intensity
            idx_min = forecast_window['predicted'].idxmin()

            # Shift the power utilization to the time with minimum forecasted carbon intensity
            merged_df_copy.at[idx_min, 'shifted_power_util'] += merged_df_copy.at[i, 'measured_power_util']

    # Calculate the emissions
    merged_df_copy['emissions'] = merged_df_copy['shifted_power_util'] * merged_df_copy['actual']

    # Calculate peak power utilization and total carbon emissions
    peak_power_utilization = merged_df_copy['shifted_power_util'].max()
    total_carbon_emissions = merged_df_copy['emissions'].sum()

    # Append the results to the lists
    peak_power_utilization_list.append(peak_power_utilization)
    total_carbon_emissions_list.append(total_carbon_emissions)

# Plotting the results on one graph with dual y-axes
fig, ax1 = plt.subplots(figsize=(12, 6))

# Plot total carbon emissions on the left y-axis
color = 'tab:blue'
ax1.set_xlabel('Shift Window (hours)')
ax1.set_ylabel('Total Carbon Emissions (gCO2)', color=color)
ax1.plot(shift_windows, total_carbon_emissions_list, marker='o', linestyle='-', color=color, label='Total Carbon Emissions')
ax1.tick_params(axis='y', labelcolor=color)
ax1.grid(True)

# Instantiate a second axes that shares the same x-axis
ax2 = ax1.twinx()

# Plot peak power utilization on the right y-axis
color = 'tab:red'
ax2.set_ylabel('Peak Power Utilization (kWh)', color=color)
ax2.plot(shift_windows, peak_power_utilization_list, marker='o', linestyle='-', color=color, label='Peak Power Utilization')
ax2.tick_params(axis='y', labelcolor=color)

# Add a title and legend
plt.title('Total Carbon Emissions and Peak Power Utilization vs Shift Window')
fig.tight_layout()  # Adjust layout to prevent clipping

# Combine legends from both axes
lines_1, labels_1 = ax1.get_legend_handles_labels()
lines_2, labels_2 = ax2.get_legend_handles_labels()
ax1.legend(lines_1 + lines_2, labels_1 + labels_2, loc='upper right')

plt.savefig(f'{ciso_name}_power_utilization_analysis_shift_24hrs.png')

plt.show()

