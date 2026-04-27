import os
import rasterio
import numpy as np

# Path to the folder containing raster files
path = "C:/Users/RDCRLSMC/Desktop/snowdepth/"
files = os.listdir(path)
# sortList = 0, 3, 4, 1, 2
# files = files[sortList]
print(files)

def calculate_raster_medians(folder_path):
    # List all raster files in the folder
    raster_files = [os.path.join(folder_path, f) for f in os.listdir(folder_path) if f.endswith('.tif')]
    # Dictionary to store median values for each raster
    raster_medians = {}

    for raster_file in raster_files:

        with rasterio.open(raster_file) as src:
            # Read the data as a 2D numpy array (assuming single band rasters)
            data = src.read(1)

            # Compute median and store
            median_value = np.nanmedian(data)
            raster_medians[raster_file] = median_value

    return raster_medians

rastermedians = calculate_raster_medians(path)
print(rastermedians)