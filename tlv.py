from struct import *

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
	return int(binaryData)         #return parseInt(binaryData.toString('hex'), 16);

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
		raise ValueError('Given argument is not a buffer');


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



