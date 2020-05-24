FROM swr.cn-north-4.myhuaweicloud.com/geogenius_dev/geogenius-sdk-cpu-py3:latest
ADD ./car-detection.tar.gz /opt
WORKDIR /opt/car-detection
RUN ["/opt/conda/bin/python", "setup.py", "install"]
