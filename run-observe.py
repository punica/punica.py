from restapi import Service
from restapi import Device
service = Service()
device = Device(service, 'urn:uuid:68af2414-7eb7-4c59-bf17-394e9a0e5544')
service.start()

def function_callback(code, data):
	print(code)
	print(data)
	
device.observe('/3315/2/5700', function_callback)
