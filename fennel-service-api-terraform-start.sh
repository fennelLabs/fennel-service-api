 #!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin us-east1-docker.pkg.dev
docker run -dit -p 1234:1234 --name fennel-service-api us-east1-docker.pkg.dev/whiteflag-0/fennel-docker-registry/fennel-service-api:latest
docker exec -it fennel-service-api sh
cd /opt/app
./build-dev.sh