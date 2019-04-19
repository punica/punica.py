pylint --rcfile=.pylint_conf *.py tests/*.py
cd tests
openssl genrsa -out test.key 2048
openssl req -days 365 -new -x509 -key test.key -out test.pem -subj '/CN=localhost'
cd ..
openssl genrsa -out server.key 2048
openssl req -days 365 -new -x509 -key server.key -out server.pem -subj '/CN=localhost'
coverage run -m tests
coverage report -m
