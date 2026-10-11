import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#load data set
#replace ? with 0
data = pd.read_csv('farr.csv', na_values='?').fillna(0)
#data = pd.read_csv('farr.csv')
print(data.head())

#print total years in the data set
total_years = data['year'].nunique()
print(f'Total years in the data set: {total_years}')
#print total number of rows in the data set
total_rows = data.shape[0]
print(f'Total number of rows in the data set: {total_rows}')    
#print any missing values in the data set
missing_values = data.isnull().sum()
print(f'Missing values in the data set:\n{missing_values}')





fig, ax = plt.subplots(subplot_kw={"projection": "polar"}, figsize=(4, 4))

#set 0˚ at top
ax.set_theta_zero_location("N") 
#clockwise
ax.set_theta_direction(-1)        
ax.set_ylim(0, 1) #radius 1
ax.set_xticks([]) #clear
ax.set_yticks([])

#planning
weeks = np.arange(1, 53)
angles = 2 * np.pi * (weeks - 1) / 52 #starts with week 1 at 0˚ (also r = 1)
#print(angles[0], angles[-1], 2 * np.pi)
#plt.show()



#temps in week order
YEAR = 1846 #testing purposes
year_df = data[data['year'] == YEAR].sort_values('week')
temp = year_df['mean_temperature'].to_numpy()
temp = np.where(temp == 0, np.nan, temp)

#reference_temp is constant at 48.4, take first value
temp_ref = year_df['temperature_reference'].iloc[0]

#deviation from reference
dev = temp - temp_ref
print(np.nanmin(dev), np.nanmax(dev))
#make dev the radius
BASE_R = 0.3
SCALE = 0.012
curve_r = BASE_R + dev * SCALE

#close loop
angles_closed = np.append(angles, angles[0] + 2 * np.pi)
curve_closed = np.append(curve_r, curve_r[0])
base_closed = np.full_like(curve_closed, BASE_R)

#baseline
full = np.linspace(0, 2 * np.pi, 200)
ax.plot(full, np.full_like(full, BASE_R), "k--", lw=0.8)

#fill area between baseline and curve
ax.fill_between(angles_closed, base_closed, curve_closed, color="tab:red", alpha=0.6)
ax.plot(angles_closed, curve_closed, "k", lw=0.5)

#plt.show()

#true when outside  baseline (hotter) or inside it (colder)
above = curve_closed >= base_closed
below = curve_closed <= base_closed

#same arrays, one colour each
ax.fill_between(angles_closed, base_closed, curve_closed,
                where=above, interpolate=True, color="tab:red", alpha=0.6)
ax.fill_between(angles_closed, base_closed, curve_closed,
                where=below, interpolate=True, color="tab:blue", alpha=0.6)
#outline
ax.plot(angles_closed, curve_closed, "k", lw=0.5)
plt.show()