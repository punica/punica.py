pylint --rcfile=.pylint_conf *.py tests/*.py
coverage run -m tests
coverage report -m
