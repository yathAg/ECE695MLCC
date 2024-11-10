import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Control variables
generate_text = False
generate_image = False
generate_csv = False  # Set to False to avoid generating multiple CSV files

# Define dataset and paths
ciso_name = 'CISO'  # Define the name of the CISO dataset
power_trace_path = Path('..') / 'data_powerTrace' / 'cella_pdu6_converted.csv'
ci_data_path = Path('..') / 'data_SPC24' / f'SPCI-{ciso_name}' / f'{ciso_name}_direct_24hr_CI_forecasts_spci__alpha_0.1.csv'

# Read the CSV files with proper datetime parsing
power_trace_df = pd.read_csv(power_trace_path, parse_dates=['hour'])
ci_data_df = pd.read_csv(ci_data_path, parse_dates=['datetime'])

# Rename the 'hour' column to 'datetime' for consistency
power_trace_df.rename(columns={'hour': 'datetime'}, inplace=True)

# Use the midpoint of the confidence interval as the forecasted carbon intensity
ci_data_df['ci_midpoint_forecast'] = (ci_data_df['lower bound'] + ci_data_df['upper bound']) / 2

# Rename columns for consistency
ci_data_df.rename(columns={'actual': 'carbon_intensity_actual',
                           'predicted': 'avg_carbon_intensity_predicted'}, inplace=True)

# Merge the two DataFrames on 'datetime'
merged_df = pd.merge(power_trace_df, ci_data_df, on='datetime')

# Initialize lists to store results
shift_windows = list(range(0, 25))  # Shift windows from 0 to 24 inclusive

# Results for using ci_midpoint_forecast
total_emissions_ci = []
peak_power_utilization_ci = []

# Results for using avg_carbon_intensity_predicted
total_emissions_predicted = []
peak_power_utilization_predicted = []

# Calculate the average power utilization without optimization
average_power_utilization = merged_df['measured_power_util'].mean()

# Define the max peak power as a multiple of the average power utilization
# Since you want only one parameter, we'll fix the power multiplier at 1
power_multiplier = 5
max_peak_power = power_multiplier * average_power_utilization

# Function to perform workload shifting
def perform_shifting(df, forecast_column, shift_window):
    df = df.copy()
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
    
            # Use the specified forecast column for sorting
            forecast_window['forecast_for_sorting'] = forecast_window[forecast_column]
    
            # Sort the window by the forecasted carbon intensity, lowest first
            sorted_window = forecast_window.sort_values(by='forecast_for_sorting')
    
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
    
    # Calculate the emissions using shifted power utilization and actual carbon intensity
    df['emissions'] = df['shifted_power_util'] * df['carbon_intensity_actual']
    
    # Calculate peak power utilization and total carbon emissions
    peak_power_utilization = df['shifted_power_util'].max()
    total_carbon_emissions = df['emissions'].sum()
    
    return total_carbon_emissions, peak_power_utilization, df

# Loop over shift windows
for shift_window in shift_windows:
    # Using ci_midpoint_forecast
    emissions_ci, peak_power_ci, df_ci = perform_shifting(
        merged_df, 'ci_midpoint_forecast', shift_window)
    total_emissions_ci.append(emissions_ci)
    peak_power_utilization_ci.append(peak_power_ci)
    
    # Using avg_carbon_intensity_predicted
    emissions_predicted, peak_power_predicted, df_predicted = perform_shifting(
        merged_df, 'avg_carbon_intensity_predicted', shift_window)
    total_emissions_predicted.append(emissions_predicted)
    peak_power_utilization_predicted.append(peak_power_predicted)
    
    # Optional: Generate CSV files for each shift window and method
    if generate_csv:
        df_ci.to_csv(f'full_data_shift_{shift_window}_peak_{max_peak_power:.2f}_ci.csv', index=False)
        df_predicted.to_csv(f'full_data_shift_{shift_window}_peak_{max_peak_power:.2f}_predicted.csv', index=False)
    
    # Optional: Generate text reports
    if generate_text:
        with open(f'analysis_shift_{shift_window}_peak_{max_peak_power:.2f}_ci.txt', 'w') as f:
            f.write(f"Shift Window: {shift_window} hours (Using CI Midpoint Forecast)\n")
            f.write(f"Max Peak Power Limit: {max_peak_power:.2f} kWh\n")
            f.write(f"Peak Power Utilization: {peak_power_ci:.2f} kWh\n")
            f.write(f"Total Carbon Emissions: {emissions_ci:.2f} gCO2\n")
        with open(f'analysis_shift_{shift_window}_peak_{max_peak_power:.2f}_predicted.txt', 'w') as f:
            f.write(f"Shift Window: {shift_window} hours (Using Predicted Carbon Intensity)\n")
            f.write(f"Max Peak Power Limit: {max_peak_power:.2f} kWh\n")
            f.write(f"Peak Power Utilization: {peak_power_predicted:.2f} kWh\n")
            f.write(f"Total Carbon Emissions: {emissions_predicted:.2f} gCO2\n")

# Plot total emissions vs. shift window for both methods
plt.figure(figsize=(10,6))
plt.plot(shift_windows, total_emissions_ci, marker='o', label='Using CI Midpoint Forecast')
plt.plot(shift_windows, total_emissions_predicted, marker='s', label='Using Predicted Carbon Intensity')
plt.title('Total Carbon Emissions vs. Shift Window Size')
plt.xlabel('Shift Window Size (hours)')
plt.ylabel('Total Carbon Emissions (gCO2)')
plt.legend()
plt.grid(True)
plt.show()
