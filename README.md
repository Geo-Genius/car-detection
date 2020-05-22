Docker build step:
=====
1. fetch target branch code:
```
git clone ssh://git@code-cbu.huawei.com:2233/geogenius/geogenius-tools.git
cd geogenius-tools
git fetch origin master:master
git checkout master
```
2. package the car detection tools:
```
cd geogenius-tools
tar -zcvf car-detection.tar.gz car-detection/
```

3. put `car-detection.tar.gz` and `Dockerfile` under same empty folder, for example:
```
mkdir -p /opt/docker
cp car-detection.tar.gz /opt/docker/
cp car-detection/Dockerfile /opt/docker/
```
4. build object-extraction image:
```
cd /opt/docker/
```
build command:
```
FROM swr.cn-north-5.myhuaweicloud.com/geogenius_dev/geogenius-python-sdk:tool0.4
ADD ./car-detection.tar.gz /opt
WORKDIR /opt/car-detection
RUN ["/opt/conda/bin/python", "setup.py", "install"]
```
5. upload the image to swr:
login swr:
docker build -t car-detection:v1.0 .
```
docker login -u cn-north-5@xxx -p xxx swr.cn-north-5.myhuaweicloud.com
```
tag image:
```
docker tag object-extraction:v0.1 swr.cn-north-5.myhuaweicloud.com/geogenius_dev/object-extraction:v0.1 
```
push image to swr:
```
docker push swr.cn-north-5.myhuaweicloud.com/geogenius_dev/object-extraction:v0.1
```


Docker env
======
follow environments need to be set when execute Dockerfile:
```
ACCESS_KEY=ak
SECRET_KEY=secret key
```

Usage
======
### rio predict --help
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
rio detection --p obs://geogenius-bucket/postam/top_potsdam_2_13_RGBIR.tif --a 120 30 121 124 --o obs://geogenius-bucket/car_detection_2_13.geojson
```

## Json Doc
注册工具body
```json
{
    "name": "geogenius-tool-car_detection-test",
    "version": "1.0",
    "description": "Use DANet Model to Extract Object",
    "inputParameters": [
        {
            "name": "cat_ids",
            "paramType": "STRING",
            "description": "data catalog ids",
            "isRequired": false,
            "multiple": false
        },
        {
            "name": "paths",
            "paramType": "STRING",
            "description": "obs paths",
            "isRequired": false,
            "multiple": false
        },
        {
            "name": "aoi",
            "paramType": "STRING",
            "description": "area of the interest",
            "isRequired": false,
            "multiple": false
        }
    ],
	"outputParameters": [
	  {
            "name": "output",
            "paramType": "FILE",
            "description": "The output COG file",
            "isRequired": false,
            "multiple": false
        }
	],
    "toolType": "Docker",
    "executorEngineDescriptor": {
        "cmd": "rio detection --cat_ids ${cat_ids} --paths ${paths} --aoi ${aoi} --output ${output}",
        "docker": {
            "image": "swr.cn-north-5.myhuaweicloud.com/geogenius_dev/car-detection:latest"
        }
    }
}
```

docker tag car_detection:latest [华为云SWR镜像名]
