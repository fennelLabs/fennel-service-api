#!/bin/bash

function all() {
  migrate
  pip3 install -r requirements.txt
  python3 -m safety check -r requirements.txt
  python3 manage.py check
  run_tests
  static
  setup
}

function all_no_tests() {
  migrate
  pip3 install -r requirements.txt
  python3 -m safety check -r requirements.txt
  python3 manage.py check
  static
  setup
}

function run_tests() {
  coverage run manage.py test -v 2
}

function clean() {
  files=$(find . -name "__pycache__")
  files2=$(find . -iregex ".*\.\(pyc\)")
  rm -rf "${files2}"
  rm -rf "${files}"
}

function migrate() {
  pwd
  python3 manage.py makemigrations main
  python3 manage.py makemigrations dashboard
  python3 manage.py makemigrations
  python3 manage.py migrate
}

function makemigrations() {
  python3 manage.py makemigrations main
  python3 manage.py makemigrations dashboard
  python3 manage.py makemigrations
}

function static() {
  python3 manage.py collectstatic --no-input
}

function run() {
  python3 manage.py runserver 0.0.0.0:8080
}

function shell() {
  python3 manage.py shell
}

function check() {
  # We're going to ignore E1101, since Django exposes members to Model classes
  # that PyLint can't see.
  clear && \
   black . && \
   pylint main --disable=E1101,W0613,R0903,C0301,C0114,C0115,C0116,R0801,E203 && \
   pylint dashboard --disable=E1101,W0613,R0903,C0301,C0114,C0115,C0116,R0801,E203 && \
   flake8 main --count --extend-ignore E1101,W0613,R0903,C0301,C0114,C0115,C0116,R0801,E203 --exclude ./main/migrations,./main/tests --max-complexity=10 --max-line-length=127 --statistics
   flake8 dashboard --count --extend-ignore E1101,W0613,R0903,C0301,C0114,C0115,C0116,R0801,E203 --exclude ./dashboard/migrations,./dashboard/tests --max-complexity=10 --max-line-length=127 --statistics
}

function gunicorn_run() {
  gunicorn --workers=8 --threads=8 --max-requests=8 fennel.wsgi:application --bind 0.0.0.0:1234
}

function setup() {
  python3 manage.py createadmin
}

mkdir -p profile
case "$1" in

check)
  migrate
  check
  ;;

startapp)
  python3 manage.py startapp "$2"
  ;;

clean)
  clean
  ;;

migrate)
  migrate
  ;;

test)
  run_tests
  ;;

run)
  run
  ;;

init-all-run)
  all
  gunicorn_run
  ;;

init-all-run-prod)
  all_no_tests
  gunicorn_run
  ;;

docker-init-all)
  check
  all
  ;;

all-run)
  check
  all
  run
  ;;

all)
  all
  ;;

makemigrations)
  makemigrations
  ;;

shell)
  shell
  ;;

esac
