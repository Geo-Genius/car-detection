Docker env
======
follow environments need to be set when execute Dockerfile:
```
ACCESS_KEY=ak
SECRET_KEY=secret key
MANAGER_ENDPOINT=xxx
USER_ENDPOINT=xxx
RDA_ENDPOINT=xxx
```

Usage
======
### rio detection --help
```
Usage: rio detection [OPTIONS]

  Use AI Model to Detect Cars.

Options:
  --cat_ids, --c TEXT      catalog id list for predict
  --paths, --p TEXT        obs path list for predict
  --aoi, --a FLOAT...      aio for predict
  --output_path, --o TEXT  the output path for result
  --help                   Show this message and exit.
```
* examples:
```
rio detection --p obs://your-bucket/postam/top_potsdam_2_13_RGBIR.tif --a 120 30 121 124 --o obs://your-bucket/car_detection_2_13.geojson
```

