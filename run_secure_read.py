from punica_api import Service
from punica_api import Device
from tlv import *

options = {
	'host' : 'https://localhost:8888',
	'ca' : './certificate.pem',
	'authentication' : True,
	'username' : 'admin',
	'password' : 'not-same-as-name',
	'interval' : 1.234,
	'polling' : True,
	'port' : 5725
}

read_resource_path = '/3312/0/5850'
read_resource_type = RESOURCE_TYPE['BOOLEAN']

service = Service(options);
device = Device(service, 'threeSeven');

service.start();
resource_read = {
	'identifier': int(read_resource_path.split('/')[3]),
	'type': read_resource_type
};

def read_callback(code, data):
	print decodeResource(bytearray(data.decode('base64')), resource_read);
	service.stop();

device.read(read_resource_path, read_callback);

