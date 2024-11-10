import pandas as pd

# Replace 'input.csv' with the name of your CSV file
df = pd.read_csv('raw_ISNE_direct_24hr_CI_forecasts.csv')

# Select the columns we need
columns_to_keep = ['datetime', 'carbon_intensity_actual', 'avg_carbon_intensity_forecast', 'error']

# Filter the DataFrame to only keep the necessary columns
df = df[columns_to_keep]

# Generate a new datetime column starting from 2022-07-01 0:00:00 with hourly increments
df['datetime'] = pd.date_range(start='2022-07-01 0:00:00', periods=len(df), freq='H')

# Save the filtered DataFrame to a CSV file without the index
df.to_csv('ISNE_direct_24hr_CI_forecasts.csv', index=False)
