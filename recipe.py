#!/usr/bin/env python3


import matplotlib.pyplot as plt
import nibabel as nib
import numpy as np
import pathlib
import urllib.request
import zipfile


# Paths. Atlas: https://nist.mni.mcgill.ca/icbm-152-nonlinear-atlases-2009/
url = 'https://www.bic.mni.mcgill.ca/~vfonov/icbm/2009/mni_icbm152_nlin_sym_09a_nifti.zip'
zip_file = pathlib.Path(pathlib.Path(url).name)
zip_data = pathlib.Path(zip_file.name.removesuffix('.zip'))


# Download.
if not zip_file.exists():
    urllib.request.urlretrieve(url, zip_file)


# Extract.
if not zip_data.exists():
    with zipfile.ZipFile(zip_file, 'r') as f:
        f.extractall(zip_data)


# Loading. Image, brain mask, tissue probability maps.
d = zip_data / 'mni_icbm152_nlin_sym_09a'
t1 = nib.load(d / 'mni_icbm152_t1_tal_nlin_sym_09a.nii')
fg = nib.load(d / 'mni_icbm152_t1_tal_nlin_sym_09a_mask.nii')
gm = nib.load(d / 'mni_icbm152_gm_tal_nlin_sym_09a.nii')
wm = nib.load(d / 'mni_icbm152_wm_tal_nlin_sym_09a.nii')
csf = nib.load(d / 'mni_icbm152_csf_tal_nlin_sym_09a.nii')


def get_slice(image, win=185, dx=6, dy=0):
    """Extract a coronal square slice.

    Parameters
    ----------
    image : nib.spatialimages.SpatialImage
        NiBabel image.
    win : int, optional
        Side length of the square slice.
    dx : int, optional
        Horizontal offset applied to the slice.
    dy : int, optional
        Vertical offset applied to the slice.

    Returns
    -------
    slice : (win, win) np.ndarray
        2D image slice (win, win).

    """
    # Select a central slice.
    image = image.dataobj[:, 100, :]

    # Transpose, then flip vertically.
    image = np.flipud(image.T)

    # Extract a shifted square view.
    return image[dy:dy + win, dx:dx + win]


# Slice selection. Create a discrete-valued label maps from the tissue
# probability maps, restricted to the brain mask.
mask = get_slice(fg)
image = get_slice(t1)
labels = [get_slice(i) for i in (gm, wm, csf)]
labels = (np.zeros_like(image), *labels) * mask
labels = np.argmax(labels, axis=0)


# Colors. Define non-zero RGBA values for gray and white matter. The rightmost
# value is A, short for alpha: 0 means transparent, 1 means opaque.
rgba = np.zeros((*image.shape, 4))
rgba[labels == 1] = (0.33, 0.20, 0.80, 0.70)
rgba[labels == 2] = (0.65, 0.50, 0.80, 0.60)


# Figure. Axis: left, bottom, width, and height relative to figure dimensions.
fig = plt.figure(figsize=(1, 1), dpi=300)
ax = fig.add_axes((0, 0, 1, 1))


# Plot.
ax.imshow(image, cmap='gray')
ax.imshow(rgba)
ax.axis('off')


# Output. Use 300-600 dots per inch (DPI) for high-quality PNG exports.
fig.savefig('overlay.png', dpi=300)
