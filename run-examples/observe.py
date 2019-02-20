from punica import Service
from punica import Device
from tlv import RESOURCE_TYPE, encode_resource, decode_resource

DEVICE_ID = 'threeSeven'
WRITE_RESOURCE_PATH = '/1/0/3'
WRITE_RESOURCE_TYPE = RESOURCE_TYPE['INTEGER']
WRITE_RESOURCE_VALUE = 3
OBSERVE_RESOURCE_PATH = '/3312/0/5850'
OBSERVE_RESOURCE_TYPE = RESOURCE_TYPE['BOOLEAN']

SERVICE = Service()
DEVICE = Device(SERVICE, 'threeSeven')
SERVICE.start()

RESOURCE_OBSERVE = {
    'identifier': int(OBSERVE_RESOURCE_PATH.split('/')[3]),
    'type': OBSERVE_RESOURCE_TYPE
}


def observe_callback(code, data):
    print decode_resource(bytearray(data.decode('base64')), RESOURCE_OBSERVE)
    DEVICE.cancel_observe(OBSERVE_RESOURCE_PATH)
    SERVICE.stop()


RESOURCE_WRITE = {
    'identifier': int(WRITE_RESOURCE_PATH.split('/')[3]),
    'type': WRITE_RESOURCE_TYPE,
    'value': WRITE_RESOURCE_VALUE
}
ENCODED_RESOURCE_WRITE = encode_resource(RESOURCE_WRITE)


def write_callback(code, data):
    print 'WRITE COMPLETED, status:', code
    DEVICE.observe(OBSERVE_RESOURCE_PATH, observe_callback)


DEVICE.write(WRITE_RESOURCE_PATH, write_callback, ENCODED_RESOURCE_WRITE)
