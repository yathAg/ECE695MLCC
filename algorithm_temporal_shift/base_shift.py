import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# Read the CSV files with proper datetime parsing
pdu_path = Path('..') / 'Power_trace' / 'cella_pdu6_time_converted_hourly.csv'
ciso_path = Path('..') / 'CI_trace' / 'CISO.csv'

pdu_df = pd.read_csv(pdu_path, parse_dates=['hour'])
ciso_df = pd.read_csv(ciso_path, parse_dates=['datetime'])

# Rename the 'hour' column to 'datetime' for consistency
pdu_df.rename(columns={'hour': 'datetime'}, inplace=True)

# Merge the two DataFrames on 'datetime'
merged_df = pd.merge(pdu_df, ciso_df, on='datetime')

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
        forecast_window = merged_df.iloc[i:end_idx]
        
        # Find the index with the minimum forecasted carbon intensity
        idx_min = forecast_window['avg_carbon_intensity_forecast'].idxmin()
        
        # Shift the power utilization to the time with minimum forecasted carbon intensity
        merged_df.at[idx_min, 'shifted_power_util'] += merged_df.at[i, 'measured_power_util']

# Calculate the emissions
merged_df['emissions'] = merged_df['shifted_power_util'] * merged_df['carbon_intensity_actual']

# Calculate peak power utilization and total carbon emissions
peak_power_utilization = merged_df['shifted_power_util'].max()
total_carbon_emissions = merged_df['emissions'].sum()

# Save the peak power utilization and total emissions to a text file
with open(f'analysis_shift_{shift_window}.txt', 'w') as f:
    f.write(f"Shift Window: {shift_window} hours\n")
    f.write(f"Peak Power Utilization: {peak_power_utilization:.2f} kWh\n")
    f.write(f"Total Carbon Emissions: {total_carbon_emissions:.2f} gCO2\n")

# Save the full merged DataFrame to a CSV file
merged_df.to_csv(f'full_data_shift_{shift_window}.csv', index=False)

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
    plt.title('Shifted Power Utilization')
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

# Save the plot as a PNG file with shift_window value in the name
plt.savefig(f'power_utilization_analysis_shift_{shift_window}.png')

# Display the plot
plt.show()