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
export FENNEL_CLI_IP=https://bitwise.fennellabs.com
export FENNEL_SUBSERVICE_IP=https://subservice.fennellabs.com
python -m black .
./runner.sh all
