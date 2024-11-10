import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# New control variables
generate_text = False
generate_image = False
generate_csv = True

# Define dataset and paths
ciso_name = 'CISO'  # Define the name of the CISO dataset
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

# Define the max peak power as a multiple of the average power utilization
power_multiplier = 100  # You can change this factor as needed
max_peak_power = power_multiplier * average_power_utilization

# Define the shift window (in hours)
shift_window = 12  # You can change this value as needed

# Check if shift_window is 0 to skip optimization
if shift_window == 0:
    # No optimization; use original measured power utilization
    merged_df['shifted_power_util'] = merged_df['measured_power_util']
else:
    # Initialize shifted_power_util to zeros
    merged_df['shifted_power_util'] = 0.0

    # Total number of data points
    num_rows = len(merged_df)

    # Iterate over each time point
    for i in range(num_rows):
        # Determine the window of future hours to consider
        end_idx = min(i + shift_window, num_rows)

        # Extract the forecasted carbon intensities in the window
        forecast_window = merged_df.iloc[i:end_idx].copy()

        # Sort the window by carbon intensity forecast, lowest first
        sorted_window = forecast_window.sort_values(by='avg_carbon_intensity_forecast')

        # Initialize a flag to check if workload has been shifted
        shifted = False

        # Find a suitable time within the window that doesn't exceed max_peak_power
        for idx in sorted_window.index:
            # Calculate potential new power utilization
            potential_power_util = merged_df.at[idx, 'shifted_power_util'] + merged_df.at[i, 'measured_power_util']

            # Check if this shift would exceed max_peak_power
            if potential_power_util <= max_peak_power:
                # If within limit, shift the power utilization to this time slot
                merged_df.at[idx, 'shifted_power_util'] = potential_power_util
                shifted = True
                break

        # If no suitable time was found, keep the workload at its original time
        if not shifted:
            merged_df.at[i, 'shifted_power_util'] += merged_df.at[i, 'measured_power_util']

    # Verify that total power utilization remains the same
    total_measured_power = merged_df['measured_power_util'].sum()
    total_shifted_power = merged_df['shifted_power_util'].sum()
    assert abs(total_measured_power - total_shifted_power) < 1e-6, "Total power utilization mismatch!"

# Calculate the emissions
merged_df['emissions'] = merged_df['shifted_power_util'] * merged_df['carbon_intensity_actual']

# Calculate peak power utilization and total carbon emissions
peak_power_utilization = merged_df['shifted_power_util'].max()
total_carbon_emissions = merged_df['emissions'].sum()

# Conditional file generation based on control variables
if generate_text:
    with open(f'analysis_shift_{shift_window}_peak_{max_peak_power:.2f}.txt', 'w') as f:
        f.write(f"Shift Window: {shift_window} hours\n")
        f.write(f"Max Peak Power Limit: {max_peak_power:.2f} kWh ({power_multiplier} times the average power utilization)\n")
        f.write(f"Peak Power Utilization: {peak_power_utilization:.2f} kWh\n")
        f.write(f"Total Carbon Emissions: {total_carbon_emissions:.2f} gCO2\n")

if generate_csv:
    merged_df.to_csv(f'full_data_shift_{shift_window}_peak_{max_peak_power:.2f}.csv', index=False)

# Plotting the results
plt.figure(figsize=(12, 10))

# Plot actual carbon intensity
plt.subplot(3, 1, 1)
plt.plot(merged_df['datetime'], merged_df['carbon_intensity_actual'], label='Actual Carbon Intensity', color='green')
plt.title('Actual Carbon Intensity')
plt.ylabel('gCO2/kWh')
plt.legend()

# Plot shifted (or original) power utilization
plt.subplot(3, 1, 2)
plt.plot(merged_df['datetime'], merged_df['shifted_power_util'], label='Power Utilization', color='blue')
if shift_window > 0:
    plt.title('Shifted Power Utilization with Max Peak Power Limit')
else:
    plt.title('Original Power Utilization (No Shifting)')
plt.ylabel('kWh')
plt.legend()

# Plot emissions
plt.subplot(3, 1, 3)
plt.plot(merged_df['datetime'], merged_df['emissions'], label='Emissions', color='red')
if shift_window > 0:
    plt.title('Emissions After Shifting')
else:
    plt.title('Emissions Without Shifting')
plt.xlabel('Time')
plt.ylabel('gCO2')
plt.legend()

plt.tight_layout()

# Conditional image generation
if generate_image:
    plt.savefig(f'power_utilization_analysis_shift_{shift_window}_peak_{max_peak_power:.2f}.png')

plt.show()
