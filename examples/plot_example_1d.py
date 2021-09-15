from bruker_utils import BrukerDataset
import matplotlib as mpl
import matplotlib.pyplot as plt


# Make font smaller
font = {'size': 8}
mpl.rc('font', **font)

dataset = BrukerDataset('data/1/pdata/1')
spectrum = dataset.data
# Note that get_samples always returns a list, even
# for 1D data, so we need to unpack it.
shifts = dataset.get_samples()[0]

# Create a figure and axes
fig = plt.figure(figsize=(4, 4))
# list elements are figure co-ordinates for:
# [left, bottom, width, height]
ax = fig.add_axes([0.03, 0.12, 0.94, 0.85])

line = ax.plot(shifts, spectrum, color='k', lw=0.8)
# The x-axis is set to be scending going from left to right
# which is the opposite to NMR convention!
# We need to flip it:
ax.set_xlim(*reversed(ax.get_xlim()))
ax.set_xlabel('$^{1}$H (ppm)')

ax.set_xticks(range(10, -2, -1))
# Don't normally show values along the y-axis
ax.set_yticks([])

# Save the figure to your preferred format
fig.savefig('spectrum_1d.pdf')
