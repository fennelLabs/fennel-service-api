#!/bin/bash
export DEBUG=True
export SECRET_KEY="3HY>fXi!dQ&(7Vf.XghCa;L2G=Ul9r-Bwqh>ae0RG2vIh3ZJ%T"
export ADMIN_NAME=""
export ADMIN_EMAIL=""
export EMAIL_HOST=""
export EMAIL_PORT=""
export EMAIL_USERNAME=""
export EMAIL_PASSWORD=""
export DEFAULT_FROM_EMAIL=""
export SERVER_EMAIL=""
export ENVIRONMENT="LOCAL"
export FENNEL_CLI_IP="localhost:9031"
export FENNEL_API_IP="localhost:1234"
export FENNEL_KEYSERVER_IP="localhost"
export FENNEL_SUBSERVICE_IP="localhost:6060"
export FENNEL_PROTOCOL_BOOT_IP="localhost"
export FENNEL_PROTOCOL_VALIDATOR_IP="localhost"
export FENNEL_PROTOCOL_COLLATOR_1_IP="localhost"
export FENNEL_PROTOCOL_COLLATOR_2_IP="localhost"
python -m black .
./runner.sh init-all-run
