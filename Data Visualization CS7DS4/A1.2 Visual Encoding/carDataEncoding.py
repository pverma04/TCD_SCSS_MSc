import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.lines import Line2D


#dataset
data = pd.read_csv('cars.csv')
#quick check
#print(data.head())
#print(data.shape)
#print(data.isnull().sum())

#-------PART A-------
#chart 1: MPG by color
fig, ax = plt.subplots(figsize=(8.27, 5.85))
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
plt.savefig('chart1.png', dpi=300)
#plt.show()
plt.close(fig)


#chart 2: MPG by point size
fig, ax = plt.subplots(figsize=(8.27, 5.85))
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
plt.savefig('chart2.png', dpi=300)
#plt.show()
plt.close(fig)

#chart 3: MPG by transparency
fig, ax = plt.subplots(figsize=(8.27, 5.85))
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
plt.savefig('chart3.png', dpi=300)
#plt.show()
plt.close(fig)

#-------PART B-------
#chart 4: manufacturer by color
fig, ax = plt.subplots(figsize=(8.27, 5.85))
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
plt.savefig('chart4.png', dpi=300)
#plt.show()
plt.close(fig)

#chart 5: manufacturer by small multiples
fig, axes = plt.subplots(5, 5, figsize=(8.27, 5.85), sharex=True, sharey=True)
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
plt.savefig('chart5.png', dpi=300)
#plt.show()
plt.close(fig)

#chart 6: manufacture by orientation
fig, ax = plt.subplots(figsize = (8.27, 5.85))
makes = sorted(data['make'].unique())
angles = np.linspace(0, 120, len(makes), endpoint=False) #evenly spaced rotation angles

for i, make in enumerate(makes):
    subset = data[data['make'] == make]
    ax.scatter(
        subset['price'],
        subset['horsepower'],
        s = subset['highway-mpg'] * 5,
        marker = (3, 0, angles[i]),   # triangle rotated by angle
        color = 'steelblue',
        alpha = 0.75,
        edgecolors = 'black',
        linewidths = 0.4,
        label = make
    )
ax.set_title("Chart 6: MPG by Size, Make by Orientation")
ax.set_xlabel("Price ($)")
ax.set_ylabel("Horsepower (hp)")
ax.grid(alpha=0.2)

ax.legend(
    title = "Manufacturer",
    loc = "upper center",
    bbox_to_anchor = (0.5, -0.14),
    fontsize = 7,
    title_fontsize = 9,
    ncol = 6,
    frameon = False,
    markerscale = 0.9,
    columnspacing = 1.2,
    handletextpad = 0.4
)

plt.subplots_adjust(
    bottom = 0.32,
    top = 0.90,
    left = 0.12,
    right = 0.95
)
plt.savefig('chart6.png', dpi=300)
plt.show()
plt.close(fig)

#-------PART C-------
#chart 7: car comparision for buyers
fig, axes = plt.subplots(2, 3, figsize=(8.27, 5.85))
axes = axes.flatten()
#categories
body_styles = sorted(data['body-style'].unique())
makes = sorted(data['make'].unique())
#manufacturer colors
colors = np.vstack([
    plt.cm.tab20(np.linspace(0, 1, 20)),
    plt.cm.tab20b(np.linspace(0, 1, 2))
])
make_colors = {
    make: colors[i]
    for i, make in enumerate(makes)
}

#fuel markers
fuel_markers = {
    'gas': 'o',
    'diesel': 's'
}
engine_min = data['engine-size'].min()
engine_max = data['engine-size'].max()

for i, body in enumerate(body_styles):
    ax = axes[i]
    subset = data[data['body-style'] == body]
    for _, car in subset.iterrows():
        #engine size on outline 
        line_width = 0.3 + 1.5 * (
            (car['engine-size'] - engine_min) /
            (engine_max - engine_min)
        )

        ax.scatter(
            car['price'],
            car['horsepower'],
            s = car['highway-mpg'] * 5,
            color = make_colors[car['make']],
            marker = fuel_markers[car['fuel-type']],
            edgecolors = 'black',
            linewidths = line_width,
            alpha = 0.7
        )

    ax.set_title(body.title(), fontsize=9)
    ax.grid(alpha = 0.2)

    #same scales for all panels
    ax.set_xlim(data['price'].min() - 1000,
                data['price'].max() + 1000)
    ax.set_ylim(data['horsepower'].min() - 10,
                data['horsepower'].max() + 10)

#bottom right for legend
legend_ax = axes[5]
legend_ax.axis('off')
make_handles = [
    Line2D(
        [0], [0],
        marker = 'o',
        linestyle = 'None',
        markerfacecolor = make_colors[make],
        markeredgecolor = 'black',
        markeredgewidth = 0.3,
        markersize = 6,
        label = make
    )
    for make in makes
]

legend_ax.legend(
    handles = make_handles,
    title = "Manufacturer",
    loc = 'center',
    ncol = 2,
    fontsize = 6,
    title_fontsize = 9,
    frameon = False,
    columnspacing = 0.7,
    handletextpad = 0.3,
    labelspacing = 0.5
)

fig.suptitle("Chart 7: Car Comparison by Body Style", fontsize = 13)


fuel_legend = [
    Line2D([0], [0], marker = 'o', color = 'w',
           markerfacecolor = 'gray', markeredgecolor = 'black',
           markersize = 7, label = 'Gas'),
    Line2D([0], [0], marker = 's', color = 'w',
           markerfacecolor = 'gray', markeredgecolor = 'black',
           markersize = 7, label = 'Diesel')
]
#common axis label
fig.text(0.5, 0.12, "Price ($)", ha="center", fontsize=10)
fig.text(0.03, 0.55, "Horsepower (hp)",
         rotation = "vertical", va = "center", fontsize = 10)

#fuel type
fuel_legend = [
    Line2D([0], [0], marker='o', linestyle='None',
           markerfacecolor='gray', markeredgecolor='black',
           markersize=7, label='Gas'),
    Line2D([0], [0], marker='s', linestyle='None',
           markerfacecolor='gray', markeredgecolor='black',
           markersize=7, label='Diesel')
]

#highway MPG for bubble size
mpg_legend = [
    plt.scatter([], [], s=mpg * 5,
                color='gray', alpha=0.7,
                edgecolors='black', linewidths=0.3,
                label=f'{mpg} MPG')
    for mpg in [20, 35, 50]
]

#engine size for outline 
engine_legend = [
    Line2D([0], [0], marker='o', linestyle='None',
           markerfacecolor='white', markeredgecolor='black',
           markeredgewidth=width, markersize=8,
           label=label)
    for width, label in [
        (0.3, 'Small'),
        (1.05, 'Medium'),
        (1.8, 'Large')
    ]
]

fig.legend(
    handles=fuel_legend,
    title="Fuel Type",
    loc="lower center",
    bbox_to_anchor=(0.18, 0.01),
    ncol=2,
    fontsize=7,
    title_fontsize=8,
    frameon=False
)

fig.legend(
    handles=mpg_legend,
    title="Highway MPG",
    loc="lower center",
    bbox_to_anchor=(0.50, 0.01),
    ncol=3,
    fontsize=7,
    title_fontsize=8,
    frameon=False
)

fig.legend(
    handles=engine_legend,
    title="Engine Size (Outline)",
    loc="lower center",
    bbox_to_anchor=(0.82, 0.01),
    ncol=3,
    fontsize=7,
    title_fontsize=8,
    frameon=False
)


plt.subplots_adjust(
    left=0.12,
    right=0.96,
    top=0.84,
    bottom=0.29,
    hspace=0.60,
    wspace=0.35
)

fig.savefig("chart7.png", dpi = 300)
plt.show()