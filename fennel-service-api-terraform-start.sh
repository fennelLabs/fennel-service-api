 #!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin us-east1-docker.pkg.dev
export FENNEL_CLI_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-cli-ip.sh)
export FENNEL_API_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-api-ip.sh)
export FENNEL_KEYSERVER_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-keyserver-ip.sh)
export FENNEL_SUBSERVICE_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-subservice-ip.sh)
export FENNEL_PROTOCOL_BOOT_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-protocol-boot-ip.sh)
export FENNEL_PROTOCOL_VALIDATOR_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-protocol-validator-ip.sh)
export FENNEL_PROTOCOL_COLLATOR_1_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-protocol-collator-1-ip.sh)
export FENNEL_PROTOCOL_COLLATOR_2_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-protocol-collator-2-ip.sh)
docker run -dit -p 1234:1234 --name fennel-service-api us-east1-docker.pkg.dev/whiteflag-0/fennel-docker-registry/fennel-service-api:latest
docker exec -it fennel-service-api /opt/app/build-dev.sh