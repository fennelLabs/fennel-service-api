 #!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io
export DEBUG=False
export ADMIN_NAME="Fennel Labs"
export ADMIN_EMAIL="info@fennellabs.com"
export EMAIL_HOST=smtp.sendgrid.net
export EMAIL_PORT=465
export EMAIL_USERNAME=apikey
export EMAIL_PASSWORD=$(gsutil cat gs://whiteflag-0-admin/email_password.sh)
export DEFAULT_FROM_EMAIL="info@fennellabs.com"
export SERVER_EMAIL="info@fennellabs.com"
export SECRET_KEY=$(gsutil cat gs://whiteflag-0-admin/api-secret-key.sh)
export POSTGRES_DB=$(gsutil cat gs://whiteflag-0-admin/postgres_db.sh)
export POSTGRES_USER=postgres
export POSTGRES_PASS=$(gsutil cat gs://whiteflag-0-admin/postgres_pass.sh)
export POSTGRES_NAME=fennel-service-api
export FENNEL_CLI_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-cli-ip.sh)
export FENNEL_API_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-api-ip.sh)
export FENNEL_KEYSERVER_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-keyserver-ip.sh)
export FENNEL_SUBSERVICE_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-subservice-ip.sh)
export FENNEL_PROTOCOL_BOOT_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-protocol-boot-ip.sh)
export FENNEL_PROTOCOL_VALIDATOR_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-protocol-validator-ip.sh)
export FENNEL_PROTOCOL_COLLATOR_1_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-protocol-collator-1-ip.sh)
export FENNEL_PROTOCOL_COLLATOR_2_IP=$(gsutil cat gs://whiteflag-0-admin/fennel-protocol-collator-2-ip.sh)
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin us-east1-docker.pkg.dev
docker run -dit -p 1234:1234 --name fennel-service-api us-east1-docker.pkg.dev/whiteflag-0/fennel-docker-registry/fennel-service-api:latest
docker exec -it fennel-service-api /opt/app/build.sh