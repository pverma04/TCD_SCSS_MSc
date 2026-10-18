import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.patches import Patch

#global settings
BASE_R = 0.3
SCALE = 0.009
DEATH_BASE = 0.75
DEATH_SCALE = 0.0003


#DATA CLEANING

#load data (missing values NaN)
data = pd.read_csv('farr.csv', na_values='?')

#check missing values
print(data.isnull().sum())

#save originally missing values
data['missing_temp'] = data['mean_temperature'].isna()
data['missing_deaths'] = data['deaths'].isna()

#replace missing w ref values
data['mean_temperature'] = data['mean_temperature'].fillna(data['temperature_reference'])

data['deaths'] = data['deaths'].fillna(data['mortality_reference'])
''' 
#print total years in the data set
total_years = data['year'].nunique()
print(f'Total years in the data set: {total_years}')
#print total number of rows in the data set
total_rows = data.shape[0]
print(f'Total number of rows in the data set: {total_rows}')
'''
#CHECK DATA WITHIN RADIUS RANGE
death_radii = DEATH_BASE + (
    data['deaths'] - data['mortality_reference']
) * DEATH_SCALE
temp_radii = BASE_R + (
    data['mean_temperature'] - data['temperature_reference']
) * SCALE

#MUST BE IN [0, 1] TO AVOID CLIPPING
print("Minimum temperature radius:", temp_radii.min())
print("Maximum temperature radius:", temp_radii.max())

print("Maximum mortality radius:", death_radii.max())
print("Minimum mortality radius:", death_radii.min())

# SUMMARY DATA

#copy of data
summary_data = data.copy()

#exclude sub'ed values
summary_data.loc[summary_data['missing_temp'], 'mean_temperature'] = np.nan
summary_data.loc[summary_data['missing_deaths'], 'deaths'] = np.nan

#weekly averages
summary = summary_data.groupby('week', as_index=False).agg({
    'mean_temperature': 'mean',
    'deaths': 'mean',
    'temperature_reference': 'mean',
    'mortality_reference': 'mean'
})

#weeks with no observations
summary['missing_temp'] = summary['mean_temperature'].isna()
summary['missing_deaths'] = summary['deaths'].isna()

#replace missing with ref values
summary['mean_temperature'] = summary['mean_temperature'].fillna(summary['temperature_reference'])
summary['deaths'] = summary['deaths'].fillna(summary['mortality_reference'])

#separate identifier for summary
summary['year'] = 9999
 

#legend
legend_items = [
    Patch(facecolor="tab:red", label="Above-average temperature"),
    Patch(facecolor="tab:blue", label="Below-average temperature"),
    Patch(facecolor="black", label="Above-average mortality"),
    Patch(facecolor="gold", label="Below-average mortality"),
    Patch(facecolor="purple", label="Missing data")
]

def add_scale_guides(ax):
    full = np.linspace(0, 2 * np.pi, 200)

    #temp guides: ±10°F from the reference
    temp_plus_10 = BASE_R + 10 * SCALE
    temp_minus_10 = BASE_R - 10 * SCALE

    ax.plot(full, np.full_like(full, temp_plus_10),
            color="gray", linestyle=":", lw=0.6, alpha=0.7)
    ax.plot(full, np.full_like(full, temp_minus_10),
            color="gray", linestyle=":", lw=0.6, alpha=0.7)

    #mortality guides: ±100 deaths from the reference
    death_plus_100 = DEATH_BASE + 100 * DEATH_SCALE
    death_minus_100 = DEATH_BASE - 100 * DEATH_SCALE

    ax.plot(full, np.full_like(full, death_plus_100),
            color="gray", linestyle=":", lw=0.6, alpha=0.7)
    ax.plot(full, np.full_like(full, death_minus_100),
            color="gray", linestyle=":", lw=0.6, alpha=0.7)

def plot_year(ax, data, year):
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

    #temps in week order
    year_df = data[data['year'] == year].sort_values('week')

    #weekly temp
    temp = year_df['mean_temperature'].to_numpy()
    missing = year_df['missing_temp'].to_numpy()
    #ref temp
    temp_ref = year_df['temperature_reference'].iloc[0]
    #temp deviation
    dev = temp - temp_ref

    curve_r = BASE_R + dev * SCALE

    #close circle
    angles_closed = np.append(angles, angles[0] + 2 * np.pi)
    curve_closed = np.append(curve_r, curve_r[0])
    base_closed = np.full_like(curve_closed, BASE_R)
    missing_closed = np.append(missing, missing[0])

    #baseline
    full = np.linspace(0, 2 * np.pi, 200)
    ax.plot(full, np.full_like(full, BASE_R), "k--", lw=0.8)

    #hot in red
    ax.fill_between(
        angles_closed, base_closed, curve_closed,
        where=(curve_closed >= BASE_R) & ~missing_closed,
        interpolate=True, color="tab:red", alpha=0.7
    )

    #cold in blue
    ax.fill_between(
        angles_closed, base_closed, curve_closed,
        where=(curve_closed < BASE_R) & ~missing_closed,
        interpolate=True, color="tab:blue", alpha=0.7
    )

    #no temperature outline through missing data
    curve_visible = np.where(missing_closed, np.nan, curve_closed)
    ax.plot(angles_closed, curve_visible, "k", lw=0.5)

    #missing vals in purple
    ax.bar(
        angles[missing],
        height=0.04,
        width=2 * np.pi / 52,
        bottom=BASE_R - 0.02,
        color="purple",
        alpha=0.9
    )
    #mortality in week order
    deaths = year_df['deaths'].to_numpy()
    missing_deaths = year_df['missing_deaths'].to_numpy()

    #mortality ref
    death_ref = year_df['mortality_reference'].iloc[0]

    #deviation from mortality ref
    death_dev = deaths - death_ref

    #mortality ring settings
    death_r = DEATH_BASE + death_dev * DEATH_SCALE

    #close circle
    death_closed = np.append(death_r, death_r[0])
    death_base_closed = np.full_like(death_closed, DEATH_BASE)
    missing_deaths_closed = np.append(missing_deaths, missing_deaths[0])

    #mortality baseline
    ax.plot(full, np.full_like(full, DEATH_BASE), "k--", lw=0.8)

    #above average in black
    ax.fill_between(
        angles_closed, death_base_closed, death_closed,
        where=(death_closed >= DEATH_BASE) & ~missing_deaths_closed,
        interpolate=True, color="black", alpha=0.8
    )

    #below average in yellow
    ax.fill_between(
        angles_closed, death_base_closed, death_closed,
        where=(death_closed < DEATH_BASE) & ~missing_deaths_closed,
        interpolate=True, color="gold", alpha=0.8
    )

    #mortality outline
    death_visible = np.where(missing_deaths_closed, np.nan, death_closed)
    ax.plot(angles_closed, death_visible, "k", lw=0.5)

    #missing vals in purple
    ax.bar(
        angles[missing_deaths],
        height=0.04,
        width=2 * np.pi / 52,
        bottom=DEATH_BASE - 0.02,
        color="purple",
        alpha=0.9
    )
    add_scale_guides(ax)
    ax.set_title(str(year), fontsize = 11, pad = 8)

def add_month_labels(ax):
    month_labels = [ "Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]
    
    #approximate month start weeks
    month_weeks = [1, 5, 9, 14, 18, 22, 27, 31, 35, 40, 44, 48]
    month_angles = 2 * np.pi * (np.array(month_weeks) - 1) / 52

    ax.set_xticks(month_angles)
    ax.set_xticklabels(month_labels, fontsize = 6)
    #labels close to circle
    ax.tick_params(axis='x', pad=2)
    #remove automatic grid lines
    #ax.xaxis.grid(False)

    
#3x4 grid for all
fig, axes = plt.subplots(3, 4, subplot_kw = {"projection": "polar"}, figsize = (12, 7))

years = range(1840, 1851)
for ax, year in zip(axes.flat, years):
    plot_year(ax, data, year)

#summary data in final plot
plot_year(axes.flat[-1], summary, 9999)
axes.flat[-1].set_title("Average", fontsize = 11, pad = 4) #title for summary plot
add_month_labels(axes.flat[-1])
#move summary chart slightly downward
pos = axes.flat[-1].get_position()
axes.flat[-1].set_position([
    pos.x0,         # same left position
    pos.y0 - 0.03,  # move down a little
    pos.width,      # same width
    pos.height      # same height
])

#overall title
fig.suptitle("Temperature & Mortality of London (1840–1850)", fontsize = 16, y = 0.98)

fig.text( 0.5, 0.13,
    "Inner ring: temperature (°F) | Outer ring: weekly death counts | Dashed circles: reference values\n"
    "Dotted circles show ±10°F and ±100 deaths from the references. Weeks progress clockwise from January at 0°. Purple indicates missing values filled with reference values.",
    ha="center",
    va="center",
    fontsize=8
)

#shared legend
fig.legend(
    handles = legend_items,
    loc = "lower center",
    bbox_to_anchor=(0.5, 0.01),
    ncol = 3,
    fontsize = 8,
    frameon = False
)

#spacing adjustments
plt.subplots_adjust(
    left = 0.05,
    right = 0.95,
    top = 0.85,
    bottom = 0.25,
    wspace = 0.20,
    hspace = 0.45
)

#source credit
fig.text(
    0.5, 0.005,
    "Source: Adapted from William Farr, Temperature and Mortality of London (1840–1850), published 1852.",
    ha="center",
    va="bottom",
    fontsize=7,
    color="gray"
)

plt.show()

fig.savefig("farr_visualization.pdf", dpi=300, bbox_inches="tight")
fig.savefig("farr_visualization.png", dpi=300, bbox_inches="tight")