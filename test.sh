pylint --rcfile=.pylint_conf punica.py
cd tests	
coverage run punica_test.py
coverage run lwm2m2_tlv_test.py
coverage report -m
