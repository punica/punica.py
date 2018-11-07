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
	return int(binaryData.decode('hex_codec'), 16)          #return parseInt(binaryData.toString('hex'), 16);

def binaryToBitString(binaryData):
	return "{0:b}".format(binaryToInteger(binaryData));


def changeBufferSize(buff, start, end):
	bufferArray = []
	index = start
	if not end:
		end = len(buff)

	#if (!(buff instanceof Buffer)):
	#	print('Given argument is not a buffer')
	

	if (start < 0):
		print('Wanted buffer start is negative number')
	

	if (len(buff) < end):
		print('Buffer length is smaller than wanted buffer end')
	

	if (start > end):
		print('Wanted buffer start is larger number than end')
	

	while (index < end):
		bufferArray.push(buff[index])
		index += 1
	

	return buffer(bufferArray)


def decode(buff):
	i = None
	valueIdentifier = None
	index = 1
	valueLength = 0

	#if (!(buff instanceof Buffer)):
	#	pass
		# throw Error('Given argument is not a buffer');


	if (len(buff) < 2):
		pass
		# throw Error('Given buffer is too short to store tlv data');

	valueIdentifier = buff[index]
	index += 1

	i = index
	if ((index + (buff[0] >> 5) & 0b1) > 0): # eslint-disable-line no-bitwise
		if (buff[i] == None):
			pass
			# throw Error('Given buffer is corrupted (missing data)');
		

		valueIdentifier = (valueIdentifier << 8) + buff[i] # eslint-disable-line no-bitwise
		i += 1
	

	index = i

	if ((buff[0] >> 3) & 0b11 > 0): # eslint-disable-line no-bitwise
		while (i < (index + ((buff[0] >> 3) & 0b11))): # eslint-disable-line no-bitwise
			if (buff[i] == None):
				pass
				# throw Error('Given buffer is corrupted (missing data)');
			

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
			return unpack('b', buff)			#return buff.readInt8();
		elif len(buff) == 2:
			return unpack('>h', buff)			#return buff.readInt16BE();
		elif len(buff) == 4:
			return unpack('>i', buff)			#return buff.readInt32BE();
		else:
			print('Incorrect integer value length' + len(buff)); #throw Error(`Incorrect integer value length (${buffer.length})`);
			

	elif resource['type'] == RESOURCE_TYPE['FLOAT']:
		if len(buff) == 4:
			return unpack('>f', buff)							#return buffer.readFloatBE();
		elif len(buff) == 8:
			return unpack('>d', buff)							#return buffer.readDoubleBE();
		else:
			print('Incorrect float value length' + len(buff));	#throw Error(`Incorrect float value length (${buffer.length})`);
			
	elif resource['type'] == RESOURCE_TYPE['STRING']:
		return buff.decode('ascii');								#toString

	elif resource['type'] == RESOURCE_TYPE['STRING']:
		return binaryToBitString(buff) != '0';

	elif resource['type'] == RESOURCE_TYPE['OPAQUE']:
		return buff;

	else:
		print('Unrecognised resource type' + resource['type']);			#  throw Error(`Unrecognised resource type (${resource.type})`);



def decodeResource(buff, resource):
	print('decodeResource:')
	print(buff)
	decodedResource = decode(buff)
	resourceValue

	if (resource.identifier != decodedResource.identifier):
		print('Decoded resource TLV identifier and description identifiers do not match');

	if (decodedResource['type'] == TYPE['RESOURCE']):
		resourceValue = decodeResourceValue(decodedResource['value'], resource);
	elif (decodedResource['type'] == TYPE['MULTIPLE_RESOURCE']):
		resourceValue = decodeMultipleResourceInstancesTLV(decodedResource['value'], resource)['value'];
	else:
		print('TLV type is not resource or multiple resource');
	

	return {
		'identifier': resource.identifier,
		'type': resource['type'],
		'value': resourceValue,
		'tlvSize': decodedResource.tlvSize,
	}



