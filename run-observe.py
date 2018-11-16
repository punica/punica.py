from restapi import Service
from restapi import Device
from tlv import *

device_id = 'threeSeven';
write_resource_path = '/1/0/3'
write_resource_type = RESOURCE_TYPE['INTEGER']
write_resource_value = 3
observe_resource_path = '/3312/0/5850'
observe_resource_type = RESOURCE_TYPE['BOOLEAN']

service = Service();
device = Device(service, 'threeSeven');
service.start();

resource_observe = {
	'identifier': int(observe_resource_path.split('/')[3]),
	'type': observe_resource_type
};
def observe_callback(code, data):
	print decodeResource(bytearray(data.decode('base64')), resource_observe);
	service.stop();

resource_write = {
	'identifier': int(write_resource_path.split('/')[3]),
	'type': write_resource_type,
	'value': write_resource_value
};
encoded_resource_write = encodeResource(resource_write);
def write_callback(code, data):
	print 'WRITE COMPLETED, status:', code;
	device.observe(observe_resource_path, observe_callback);

device.write(write_resource_path, write_callback, encoded_resource_write);
