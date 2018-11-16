from struct import *
import numbers

TYPE = {
	'OBJECT_INSTANCE': 0b00,
	'MULTIPLE_RESOURCE': 0b10,
	'RESOURCE_INSTANCE': 0b01,
	'RESOURCE': 0b11
};

RESOURCE_TYPE = {
	'NONE': 0,
	'BOOLEAN': 1,
	'INTEGER': 2,
	'FLOAT': 3,
	'STRING': 4,
	'OPAQUE': 5
};

def binaryToInteger(binaryData):
	return int(binaryData)         														#return parseInt(binaryData.toString('hex'), 16);

def binaryToBitString(binaryData):
	return "{0:b}".format(binaryToInteger(binaryData[1]));		# ???

def changeBufferSize(buff, start, end):
	bufferArray = []
	index = start
	if not end:
		end = len(buff)

	if not isinstance(buff, bytearray):
		raise ValueError('Given argument is not a buffer');

	if (start < 0):
		raise ValueError('Wanted buffer start is negative number')
	

	if (len(buff) < end):
		raise ValueError('Buffer length is smaller than wanted buffer end')
	

	if (start > end):
		raise ValueError('Wanted buffer start is larger number than end')
	

	while (index < end):
		bufferArray.append(buff[index])
		index += 1
	

	return bytearray(bufferArray)


def decode(buff):
	i = None
	valueIdentifier = None
	index = 1
	valueLength = 0

	if not isinstance(buff, bytearray):
		raise ValueError('Given argument is not a bytearray');


	if (len(buff) < 2):
		raise ValueError('Given buffer is too short to store tlv data');

	valueIdentifier = buff[index]
	index += 1
	i = index
	if ((index + (buff[0] >> 5) & 0b1) > 0): # eslint-disable-line no-bitwise
		if (buff[i] == None):
			raise ValueError('Given buffer is corrupted (missing data)');
		

		valueIdentifier = (valueIdentifier << 8) + buff[i] # eslint-disable-line no-bitwise
		i += 1
	

	index = i

	if ((buff[0] >> 3) & 0b11 > 0): # eslint-disable-line no-bitwise
		while (i < (index + ((buff[0] >> 3) & 0b11))): # eslint-disable-line no-bitwise
			if (buff[i] == None):
				raise ValueError('Given buffer is corrupted (missing data)');
			

			valueLength = (valueLength << 8) + buff[i] # eslint-disable-line no-bitwise
			i += 1
		
	else:
		valueLength = buff[0] & 0b111 # eslint-disable-line no-bitwise
	index = i

	return {
		'type': buff[0] >> 6, # eslint-disable-line no-bitwise
		'identifier': valueIdentifier,
		'value': changeBufferSize(buff, index, index + valueLength),
		'tlvSize': index + valueLength
	}
	
def decodeResourceValue(buff, resource):
	if resource['type'] == RESOURCE_TYPE['INTEGER']:
		if len(buff) == 0:
			return 0;
		elif len(buff) == 1:
			return unpack('b', buff)[0]
		elif len(buff) == 2:
			return unpack('>h', buff)[0]
		elif len(buff) == 4:
			return unpack('>i', buff)[0]
		else:
			raise ValueError('Incorrect integer value length', len(buff));
			

	elif resource['type'] == RESOURCE_TYPE['FLOAT']:
		if len(buff) == 4:
			return unpack('>f', buff)[0]
		elif len(buff) == 8:
			return unpack('>d', buff)[0]
		else:
			raise ValueError('Incorrect float value length', len(buff));
			
	elif resource['type'] == RESOURCE_TYPE['STRING']:
		return buff.decode('ascii');								

	elif resource['type'] == RESOURCE_TYPE['BOOLEAN']:
		return binaryToBitString(buff) != '0';

	elif resource['type'] == RESOURCE_TYPE['OPAQUE']:
		return buff;

	else:
		raise ValueError('Unrecognised resource type', resource['type']);



def decodeResource(buff, resource):
	decodedResource = decode(buff)
	resourceValue = None

	if (resource['identifier'] != decodedResource['identifier']):
		raise ValueError('Decoded resource TLV identifier and description identifiers do not match');

	if (decodedResource['type'] == TYPE['RESOURCE']):
		resourceValue = decodeResourceValue(decodedResource['value'], resource);
	elif (decodedResource['type'] == TYPE['MULTIPLE_RESOURCE']):
		resourceValue = decodeMultipleResourceInstancesTLV(decodedResource['value'], resource)['value'];
	else:
		raise ValueError('TLV type is not resource or multiple resource');
	

	return {
		'identifier': resource['identifier'],
		'type': resource['type'],
		'value': resourceValue,
		'tlvSize': decodedResource['tlvSize']
	}


def encodeResourceValue(resource):
	MIN_INT8 = -0x80;
	MAX_INT8 = 0x7f;
	MIN_INT16 = -0x8000;
	MAX_INT16 = 0x7fff;
	MIN_INT32 = -0x80000000;
	MAX_INT32 = 0x7fffffff;

	buff = None;

	if not str(resource['type']).isdigit():
		raise ValueError('Unrecognised type ', resource['type']);


	if resource['type'] == RESOURCE_TYPE['NONE']:
		if not resource['value'].isdigit():
			raise ValueError('Unrecognised value type ', type(resource['type']));
	
		return bytearray();
			
	elif resource['type'] == RESOURCE_TYPE['INTEGER']:
		if not isinstance(resource['value'], numbers.Number):
			raise ValueError('Cannot encode ', type(resource['value']), ' as integer');
	
		if (resource['value'] >= MIN_INT8 and resource['value'] <= MAX_INT8):
			buff = bytearray(1)												#buff = Buffer.alloc(1);
			buff = pack('>b', resource['value']);			#buff.writeInt8(resource['value']);
		elif (resource['value'] >= MIN_INT16 and resource['value'] <= MAX_INT16):
			buff = bytearray(2)
			buff = pack('>h', resource['value']);
		elif (resource['value'] >= MIN_INT32 and resource['value'] <= MAX_INT32):
			buff = bytearray(4)
			buff = pack('>i', resource['value']);
		else:
			## XXX: this could be implemented with long.js module,
			## but until there's a real issue no need to add another dependency
			raise ValueError('64-bit integers are not supported');


		return buff;

	elif resource['type'] == RESOURCE_TYPE['FLOAT']:
		if not isinstance(resource['value'], numbers.Number):
			raise ValueError('Cannot encode ', type(resource['value']), ' as float');

		buff = bytearray(4)
		buff = pack('>f', resource['value']);
		return buff;

	elif resource['type'] == RESOURCE_TYPE['BOOLEAN']:
		if not isinstance(resource['value'], bool):
				raise ValueError('Cannot encode ', type(resource['value']), ' as boolean');

		if resource['value']:
			return bytearray([1])
		else:
			return bytearray([0])

	elif resource['type'] == RESOURCE_TYPE['STRING']:
		if not isinstance(resource['value'], str):
			raise ValueError('Cannot encode ', type(resource['value']), ' as string');

		return bytearray(resource['value'], 'ascii');

	elif resource['type'] == RESOURCE_TYPE['OPAQUE']:
		if not isinstance(buff, bytearray):
			raise ValueError('Cannot encode ', type(resource['value']), ' as bytearray');

		return resource['value'];

	else:
		raise ValueError('Unrecognised type: ', resource['type']);

def encode(obj):
	identifierBuffer = None;
	lengthBuffer = None;
	typeByte = 0;

	if not isinstance(obj['value'], bytearray):
		raise ValueError('Encodable object value is not a bytearray');

	if not isinstance(obj['identifier'], numbers.Number):
		raise ValueError('Encodable object identifier is not a number');
	typeByte += obj['type'] << 6;

	if (obj['identifier'] >= (1 << 8)):
		typeByte += 1 << 5;
		identifierBuffer = bytearray([
			obj['identifier'] / (1 << 8),
			obj['identifier'] % (1 << 8),
		]);
	else:
		identifierBuffer = bytearray([obj['identifier']]);


	if (len(obj['value']) >= (1 << 16)):
		typeByte += 3 << 3;

		lengthBuffer = bytearray([
			len(obj['value']) / (1 << 16),
			len(obj['value']) / (1 << 8),
			len(obj['value']) % (1 << 8),
		]);
	elif (len(obj['value']) >= (1 << 8)):
		typeByte += 2 << 3;

		lengthBuffer = bytearray([
			len(obj['value']) / (1 << 8),
			len(obj['value']) % (1 << 8),
		]);
	elif (len(obj['value']) >= (1 << 3)):
		typeByte += 1 << 3;

		lengthBuffer = bytearray([len(obj['value'])]);
	else:
		typeByte += len(obj['value']);

		lengthBuffer = bytearray([]);

	return bytearray([typeByte]) + identifierBuffer + lengthBuffer + obj['value'];

def encodeResourceInstance(resourceInstance):
  return encode({
    'type': TYPE['RESOURCE_INSTANCE'],
    'identifier': resourceInstance['identifier'],
    'value': encodeResourceValue(resourceInstance),
  });


def encodeMultipleResourcesTLV(resources):
  resourceInstancesBuffers = bytearray();

  for  index in range(len(resources['value'])):
    resourceInstancesBuffers += encodeResourceInstance({
      'type': resources['type'],
      'identifier': index,
      'value': resources['value'][index],
    });

  return encode({
    'type': TYPE['MULTIPLE_RESOURCE'],
    'identifier': resources['identifier'],
    'value': resourceInstancesBuffers,
  });


def encodeResource(resource):
	if isinstance(resource['value'], list):
		return encodeMultipleResourcesTLV(resource);


	return encode({
		'type': TYPE['RESOURCE'],
		'identifier': resource['identifier'],
		'value': encodeResourceValue(resource),
	});

