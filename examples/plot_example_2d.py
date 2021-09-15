import re
from bruker_utils import BrukerDataset
import matplotlib as mpl
import matplotlib.pyplot as plt


def format_nucleus(nucleus: str) -> str:
    """Format nucleus for matplotlib."""
    match = re.search(r'^<(\d+)([A-Z]+)>$', nucleus)
    number = match.group(1)
    symbol = match.group(2)
    return f'$^{{{number}}}${symbol}'


# Make font smaller
font = {'size': 8}
mpl.rc('font', **font)

# Extract spectrum, chemical shifts, and contour levels
# from the dataset
dataset = BrukerDataset('data/2/pdata/1')
spectrum = dataset.data
shifts = dataset.get_samples()
levels = dataset.contours

# Create a figure and axes
fig = plt.figure(figsize=(4, 4))
# list elements are figure co-ordinates for:
# [left, bottom, width, height]
ax = fig.add_axes([0.14, 0.12, 0.83, 0.85])

# Make a contour plot of the spectrum
contour = ax.contour(*shifts, spectrum, levels=levels, colors='k',
                     linewidths=0.6)

# Set x- and y-limit to select the region of interest.
# Note that in each case the order of arguments is (high, low)
# to ensure the axes are flipped.
ax.set_xlim(30.39, 8.2)
ax.set_ylim(2.546, 0.541)

ax.set_xticks([x / 10 for x in range(300, 75, -25)])
ax.set_yticks([x / 10 for x in range(25, 5, -2)])


# Labels for axes.
# This snippet shows how it can be done in an automated fashion
# by extracting the `NUC1` parameter from each acquisition file.
# Also see `format_nucleus` above.
params = dataset.get_parameters(filenames=['acqus', 'acqu2s'])
xnuc = params['acqus']['NUC1']
ynuc = params['acqu2s']['NUC1']
ax.set_xlabel(f'{format_nucleus(xnuc)} (ppm)')
ax.set_ylabel(f'{format_nucleus(ynuc)} (ppm)')

# Save the figure to your preferred format
fig.savefig('spectrum_2d.pdf')
