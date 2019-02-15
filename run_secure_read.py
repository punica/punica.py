from punica import Service
from punica import Device
from tlv import RESOURCE_TYPE, decode_resource

OPTIONS = {
    'host': 'https://localhost:8888',
    'ca': './certificate.pem',
    'authentication': True,
    'username': 'admin',
    'password': 'not-same-as-name',
    'interval': 1.234,
    'polling': True,
    'port': 5725
}

READ_RESOURCE_PATH = '/3312/0/5850'
READ_RESOURCE_TYPE = RESOURCE_TYPE['BOOLEAN']

SERVICE = Service(OPTIONS)
DEVICE = Device(SERVICE, 'threeSeven')

SERVICE.start()
RESOURCE_READ = {
    'identifier': int(READ_RESOURCE_PATH.split('/')[3]),
    'type': READ_RESOURCE_TYPE
}


def read_callback(code, data):
    print decode_resource(bytearray(data.decode('base64')), RESOURCE_READ)
    SERVICE.stop()


DEVICE.read(READ_RESOURCE_PATH, read_callback)
