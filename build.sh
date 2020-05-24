cd ../
tar -zcvf car-detection.tar.gz car-detection/
mkdir -p /opt/docker
mv car-detection.tar.gz /opt/docker/
cp car-detection/Dockerfile /opt/docker/
cd /opt/docker/
docker build -t car-dection:v1.0 .
rm -rf /opt/docker
