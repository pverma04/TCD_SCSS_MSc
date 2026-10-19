import pandas as pd
import matplotlib.pyplot as plt
import numpy as np

#dataset
data = pd.read_csv('cars.csv')
#quick check
#print(data.head())
#print(data.shape)
#print(data.isnull().sum())

#-------PART A-------
#chart 1: MPG by color
fig, ax = plt.subplots(figsize = (10, 6))
scatter = ax.scatter(
    data['price'],
    data['horsepower'],
    c = data['highway-mpg'],
    cmap = 'viridis',
    s = 35,
    alpha = 0.8
)
#set up
ax.set_title("Chart 1: Price vs Horsepower (MPG by Color)") #labeling
ax.set_xlabel("Price ($)")
ax.set_ylabel("Horsepower (hp)")
cbar = plt.colorbar(scatter, ax = ax) #color
cbar.set_label("Highway MPG")
ax.grid(alpha = 0.2) #grid

plt.tight_layout()
plt.savefig('chart1.png')
#plt.show()


#chart 2: MPG by point size
fig, ax = plt.subplots(figsize = (10, 6))
sizes = data['highway-mpg'] * 5 #scale
scatter = ax.scatter(
    data['price'],
    data['horsepower'],
    s = sizes,
    color = 'steelblue',
    alpha = 0.6,
    edgecolors = 'black',
    linewidths = 0.3
)

ax.set_title("Chart 2: Price vs Horsepower (MPG by Size)") #labeling
ax.set_xlabel("Price ($)")
ax.set_ylabel("Horsepower (hp)")

for mpg in [20, 30, 40, 50]: #size legend
    ax.scatter([], [], s=mpg * 5,
               color = 'steelblue', alpha = 0.6,
               edgecolors = 'black', linewidths = 0.3,
               label = f"{mpg} MPG")

ax.legend(
    title = "Highway MPG",
    loc = "upper right",
    fontsize = 8,
    title_fontsize = 9
)

ax.grid(alpha = 0.2)

plt.tight_layout()
plt.savefig('chart2.png')
#plt.show()

#chart 3: MPG by transparency
fig, ax = plt.subplots(figsize = (10, 6))
mpg = data['highway-mpg'] #normalize MPG to opacity between 0.2 and 1.0
opacity = 0.2 + 0.8 * (mpg - mpg.min()) / (mpg.max() - mpg.min())

colors = np.zeros((len(data), 4)) #colors with transparency
colors[:, :3] = [0.1, 0.4, 0.8]
colors[:, 3] = opacity

ax.scatter(
    data['price'],
    data['horsepower'],
    c = colors,
    s = 35
)

ax.set_title("Chart 3: Price vs Horsepower (MPG by Opacity)") #labels
ax.set_xlabel("Price ($)")
ax.set_ylabel("Horsepower (hp)")

for value in [20, 30, 40, 50]: #opacity legend
    alpha = 0.2 + 0.8 * (value - mpg.min()) / (mpg.max() - mpg.min())
    ax.scatter([], [], s=35, color = (0.1, 0.4, 0.8, alpha),
               label = f"{value} MPG")

ax.legend(
    title="Highway MPG",
    loc="upper right",
    fontsize = 8,
    title_fontsize = 9
)
ax.grid(alpha = 0.2)
plt.tight_layout()
plt.savefig('chart3.png')
#plt.show()

#-------PART B-------
#chart 4: manufacturer by color
fig, ax = plt.subplots(figsize = (10, 6))
makes = sorted(data['make'].unique()) #all makes
colors = plt.cm.tab20(np.linspace(0, 1, len(makes))) #colors

for i, make in enumerate(makes):
    subset = data[data['make'] == make]
    ax.scatter(
        subset['price'],
        subset['horsepower'],
        s = subset['highway-mpg'] * 5,
        color = colors[i],
        alpha = 0.65,
        edgecolors = 'black',
        linewidths = 0.3,
        label = make
    )

ax.set_title("Chart 4: MPG by Size, Make by Color")
ax.set_xlabel("Price ($)")
ax.set_ylabel("Horsepower (hp)")

ax.legend(
    title = "Manufacturer",
    loc = "upper center",
    bbox_to_anchor = (0.5, -0.12),
    fontsize = 7,
    title_fontsize = 9,
    ncol = 6,
    frameon = False,
    markerscale = 0.6,
    columnspacing = 1.2,
    handletextpad = 0.4
)
ax.grid(alpha = 0.2)
plt.tight_layout()
plt.savefig('chart4.png')
#plt.show()

#chart 5: manufacturer by shape
fig, axes = plt.subplots(5, 5, figsize=(10, 8), sharex=True, sharey=True)
axes = axes.flatten()

makes = sorted(data['make'].unique())

#same axis for all (limits)
x_min, x_max = data['price'].min(), data['price'].max()
y_min, y_max = data['horsepower'].min(), data['horsepower'].max()

for i, make in enumerate(makes):
    ax = axes[i]
    subset = data[data['make'] == make]

    ax.scatter(
        subset['price'],
        subset['horsepower'],
        s = subset['highway-mpg'] * 5,
        color = 'steelblue',
        alpha = 0.65,
        edgecolors = 'black',
        linewidths = 0.3
    )

    ax.set_title(make, fontsize = 8)
    ax.set_xlim(x_min - 1000, x_max + 1000)
    ax.set_ylim(y_min - 5, y_max + 5)
    ax.grid(alpha = 0.2)

#hide empty
for j in range(len(makes), len(axes)):
    axes[j].set_visible(False)

#only outer labels to keep clean
for ax in axes:
    ax.label_outer()

fig.suptitle("Chart 5: MPG by Size, Make by Small Multiples", fontsize=14)

#common axis labels
fig.text(0.5, 0.15, "Price ($)", ha = "center", fontsize = 11)
fig.text(0.025, 0.55, "Horsepower (hp)", va = "center", rotation = "vertical", fontsize = 11)

#size legend
legend_sizes = [20, 30, 40, 50]
handles = [
    plt.scatter([], [], s = mpg * 5, color = 'steelblue', alpha = 0.65,
                edgecolors = 'black', linewidths = 0.3, label = f"{mpg} MPG")
    for mpg in legend_sizes
]

fig.legend(
    handles = handles,
    title = "Highway MPG",
    loc = "lower center",
    ncol = 4,
    frameon = False,
    bbox_to_anchor = (0.5, 0.0)
)

plt.subplots_adjust(
    left = 0.08,
    right = 0.98,
    top = 0.90,
    bottom = 0.12,
    hspace = 0.6,
    wspace = 0.35
)
plt.savefig('chart5.png')
#plt.show()

#chart 6: manufacture by orientation
fig, ax = plt.subplots(figsize=(6, 4))
makes = sorted(data['make'].unique())
