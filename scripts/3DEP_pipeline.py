import laspy
import glob
from os.path import join, basename, exists, dirname, abspath
import json
import requests
from glob import glob
import pdal


## After downloading a text file of LAZ tiles within AOI via https://apps.nationalmap.gov/lidar-explorer/#/, download tiles:

#Definition for downloading tiles from urls
# def download_file(url):
#     response = requests.get(url)
#     if "content-disposition" in response.headers:
#         content_disposition = response.headers["content-disposition"]
#         filename = content_disposition.split("filename=")[1]
#     else:
#         filename = url.split("/")[-1]
#     with open(filename, mode="wb") as file:
#         file.write(response.content)
#     print(f"Downloaded file {filename}")

# #Open text file
# url_list = "downloadlist_pcs.txt"

# with open(url_list, 'r') as file:
#     urls = [line.strip() for line in file if line.strip()]  # Read and strip each line

# #And download
# for url in urls:
#     download_file(url)

####Create list of unique tile collections

#list of FEMA collection
fema_fps = glob('*FEMA*.laz')
print(f"{len(fema_fps)} files into fema_fps:")
print(fema_fps)
print('----------------------------------------------------')

#SID collection
sid_fps = glob("*Southern*.laz")
print(f"{len(sid_fps)} files into sid_fps:")
print(sid_fps)


#### Merge tiles from each collection
def run_pdal_pipeline(input_files, mosaic_fp):
    pipeline = {
        "pipeline": [
            # Create the readers dynamically for each file
            *[{"type": "readers.las", "filename": fp} for fp in input_files],
            {"type": "filters.merge"},  # Merge all the files
            {"type": "writers.las", "filename": mosaic_fp}  # Output to the mosaic file
        ]
    }

    # Convert the pipeline dictionary to a JSON string
    pipeline_str = json.dumps(pipeline)

    # Create the PDAL pipeline object
    p = pdal.Pipeline(pipeline_str)

    # Execute the pipeline
    count = p.execute()

    # Print out the result
    print(f"Merged {len(input_files)} files into '{mosaic_fp}'. Processed {count} points.")

#Create destinatino for merged files
mosaic_FEMA = join('FEMA_merge.laz')
mosaic_SID = join('SID_merge.laz')

# Run the pipeline for both FEMA and SID datasets
run_pdal_pipeline(fema_fps, mosaic_FEMA)
run_pdal_pipeline(sid_fps, mosaic_SID)


####Create polygon of each dataset
# !cd "C:/Users/RDCRLSMC/Desktop/camas_3dep/laz_tiles/SouthernID_clip" && pdal tindex create --tindex boundary.sqlite --filespec SouthernID_reproject.laz -f SQLite
# !cd "C:/Users/RDCRLSMC/Desktop/camas_3dep/laz_tiles/FEMA" && pdal tindex create --tindex boundary.sqlite --filespec reproject.laz -f SQLite



##clip merged point clouds to Camas AOI
def clip_point_cloud(input_file, polygon_file, output_file):
    pipeline = [
            {
            "type": "readers.las",
            "filename": input_file
        },
        {
            "type": "filters.crop",
            "polygon": polygon_file
        },
        {
            "type": "writers.las",
            "filename": output_file
        }
    ]

    pdal_pipeline = pdal.Pipeline(json.dumps(pipeline))
    pdal_pipeline.execute()


shp = "camas_smaller.shp"

clip_point_cloud(mosaic_FEMA, shp, "FEMA_clip.laz")
clip_point_cloud(mosaic_SID, shp, "SID_clip.laz")


#### Rasterize clipped point clouds
def rasterize_pc(input_pc, output_tif):
    pipeline = [
        input_pc,
        {
            "filename": output_tif,
            "gdaldriver": "GTiff",
            "output_type": "all",
            "resolution": "1.0",
            "type": "writers.gdal"
        }
    ]
    pdal_pipeline = pdal.Pipeline(json.dumps(pipeline))
    pdal_pipeline.execute()

rasterize_pc("FEMA_clip.laz", "FEMA.tif")
rasterize_pc("SID_clip.laz", "SID.tif")


#### Transform point clouds
def transform_raster(input_pc, epsg_code, output_pc):
    pipeline = [
        {
            "type": "readers.las",
            "filename": input_pc
        },
        {
            "type": "filters.reprojection",
            "out_srs": f"EPSG:{epsg_code}"  # Use the provided epsg_code for reprojection
        },
        {
            "type": "writers.las",
            "filename": output_pc
        }
    ]
    pdal_pipeline = pdal.Pipeline(json.dumps(pipeline))
    pdal_pipeline.execute()


transform_raster("FEMA.tif","32611+4326+", "FEMA_WGS.tif")
transform_raster("SID.tif","32611+4326+", "SID_WGS.tif")