 #!/bin/bash
sudo apt-get update
sudo apt-get install -y docker.io nginx snapd
sudo snap install core && sudo snap refresh core
sudo snap install --classic certbot
sudo ln -s /snap/bin/certbot /usr/bin/certbot
gsutil cat gs://whiteflag-0-admin/fennel-nginx-conf-api.sh > /etc/nginx/sites-enabled/default
sudo systemctl enable nginx
sudo systemctl start nginx
sudo certbot --nginx --non-interactive --agree-tos --email info@fennellabs.com --domains api.fennellabs.com
sudo systemctl restart nginx
export DEBUG=False
export ADMIN_NAME="Fennel Labs"
export ADMIN_EMAIL="info@fennellabs.com"
export EMAIL_HOST=smtp.sendgrid.net
export EMAIL_PORT=587
export EMAIL_USERNAME=apikey
export EMAIL_PASSWORD=$(gsutil cat gs://whiteflag-0-admin/email_password.sh)
export DEFAULT_FROM_EMAIL="info@fennellabs.com"
export SERVER_EMAIL="info@fennellabs.com"
export SECRET_KEY=$(gsutil cat gs://whiteflag-0-admin/api-secret-key.sh)
export POSTGRES_DB=$(gsutil cat gs://whiteflag-0-admin/postgres_db.sh)
export POSTGRES_USER=postgres
export POSTGRES_PASS=$(gsutil cat gs://whiteflag-0-admin/postgres_pass.sh)
export POSTGRES_NAME=fennel_service_api
export FENNEL_CLI_IP=https://bitwise.fennellabs.com
export FENNEL_SUBSERVICE_IP=https://subservice.fennellabs.com
gcloud auth print-access-token | docker login -u oauth2accesstoken --password-stdin us-east1-docker.pkg.dev
docker run -dt -e DEBUG -e ADMIN_NAME -e ADMIN_EMAIL -e EMAIL_HOST -e EMAIL_PORT -e EMAIL_USERNAME -e EMAIL_PASSWORD -e DEFAULT_FROM_EMAIL -e SERVER_EMAIL -e SECRET_KEY -e POSTGRES_DB -e POSTGRES_USER -e POSTGRES_PASS -e POSTGRES_NAME -e FENNEL_CLI_IP -e FENNEL_SUBSERVICE_IP -p 1234:1234 --name fennel-service-api us-east1-docker.pkg.dev/whiteflag-0/fennel-docker-registry/fennel-service-api:latest
docker exec fennel-service-api /opt/app/build.sh