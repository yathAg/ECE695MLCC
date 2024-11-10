import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Read the data
# Define dataset and paths
ciso_name = 'ISNE'  # Define the name of the CISO dataset
power_trace_path = Path('..') / 'data_powerTrace' / 'cella_pdu6_converted.csv'
ci_data_path = Path('..') / 'data_SPC24' / f'SPCI-{ciso_name}' / f'{ciso_name}_direct_24hr_CI_forecasts_spci__alpha_0.1.csv'

# Read the CSV files with proper datetime parsing
power_trace_df = pd.read_csv(power_trace_path, parse_dates=['hour'])
ci_data_df = pd.read_csv(ci_data_path, parse_dates=['datetime'])

# Rename the 'hour' column to 'datetime' for consistency
power_trace_df.rename(columns={'hour': 'datetime'}, inplace=True)

# Select the relevant columns from ci_data_df
ci_data_df = ci_data_df[['datetime', 'actual', 'predicted']]
ci_data_df.rename(columns={'actual': 'carbon_intensity_actual', 'predicted': 'avg_carbon_intensity_forecast'}, inplace=True)

# Merge the two DataFrames on 'datetime'
merged_df = pd.merge(power_trace_df, ci_data_df, on='datetime')

# Calculate the average power utilization without optimization
average_power_utilization = merged_df['measured_power_util'].mean()

# Initialize a list to hold the results
results = []

# Loop over shift windows and power multipliers
for shift_window in range(25):  # 0 to 24 inclusive
    for power_multiplier in [1, 2, 5, 10, 100]:
        # Copy the merged_df to a new DataFrame to avoid modifying the original data
        df = merged_df.copy()
        
        # Define the max peak power as a multiple of the average power utilization
        max_peak_power = power_multiplier * average_power_utilization

        # Check if shift_window is 0 to skip optimization
        if shift_window == 0:
            # No optimization; use original measured power utilization
            df['shifted_power_util'] = df['measured_power_util']
        else:
            # Initialize shifted_power_util to zeros
            df['shifted_power_util'] = 0.0

            # Total number of data points
            num_rows = len(df)

            # Iterate over each time point
            for i in range(num_rows):
                # Determine the window of future hours to consider
                end_idx = min(i + shift_window, num_rows)

                # Extract the forecasted carbon intensities in the window
                forecast_window = df.iloc[i:end_idx].copy()

                # Sort the window by carbon intensity forecast, lowest first
                sorted_window = forecast_window.sort_values(by='avg_carbon_intensity_forecast')

                # Initialize a flag to check if workload has been shifted
                shifted = False

                # Find a suitable time within the window that doesn't exceed max_peak_power
                for idx in sorted_window.index:
                    # Calculate potential new power utilization
                    potential_power_util = df.at[idx, 'shifted_power_util'] + df.at[i, 'measured_power_util']

                    # Check if this shift would exceed max_peak_power
                    if potential_power_util <= max_peak_power:
                        # If within limit, shift the power utilization to this time slot
                        df.at[idx, 'shifted_power_util'] = potential_power_util
                        shifted = True
                        break

                # If no suitable time was found, keep the workload at its original time
                if not shifted:
                    df.at[i, 'shifted_power_util'] += df.at[i, 'measured_power_util']

            # Verify that total power utilization remains the same
            total_measured_power = df['measured_power_util'].sum()
            total_shifted_power = df['shifted_power_util'].sum()
            assert abs(total_measured_power - total_shifted_power) < 1e-6, "Total power utilization mismatch!"

        # Calculate the emissions
        df['emissions'] = df['shifted_power_util'] * df['carbon_intensity_actual']

        # Calculate peak power utilization and total carbon emissions
        peak_power_utilization = df['shifted_power_util'].max()
        total_carbon_emissions = df['emissions'].sum()

        # Append results to the list
        results.append({
            'shift_window': shift_window,
            'power_multiplier': power_multiplier,
            'total_carbon_emissions': total_carbon_emissions
        })

# Create a DataFrame from the results
results_df = pd.DataFrame(results)

# Pivot the DataFrame for plotting
pivot_df = results_df.pivot(index='shift_window', columns='power_multiplier', values='total_carbon_emissions')

# Plotting the results
plt.figure(figsize=(12, 8))

for power_multiplier in [1, 2, 5, 10, 100]:
    plt.plot(pivot_df.index, pivot_df[power_multiplier], marker='o', label=f'Power Multiplier {power_multiplier}')

plt.xlabel('Shift Window (hours)')
plt.ylabel('Total Carbon Emissions (gCO2)')
plt.title(f'Total Carbon Emissions vs. Shift Window for Different Power Multipliers ({ciso_name})')
plt.legend(title='Power Multiplier')
plt.grid(True)

# Save the plot with the specified filename
plot_filename = f'{ciso_name}_power_utilization_analysis_shift_24hrs.png'
plt.savefig(plot_filename)

plt.show()
