"""
This module stores LwM2M TLV parsing methods
"""
from struct import pack, unpack
import binascii
import numbers

TYPE = {
    'OBJECT_INSTANCE': 0b00,
    'MULTIPLE_RESOURCE': 0b10,
    'RESOURCE_INSTANCE': 0b01,
    'RESOURCE': 0b11
}

RESOURCE_TYPE = {
    'NONE': 0,
    'BOOLEAN': 1,
    'INTEGER': 2,
    'FLOAT': 3,
    'STRING': 4,
    'OPAQUE': 5
}


def binary_to_integer(binary_data):
    """Converts bytes to integer.

    Parameters:
    binaryData (bytearray): Buffer which will be converted.

    Returns:
    int: Integer value.
    """
    return int(binascii.hexlify(binary_data), base=16)


def binary_to_bit_string(binary_data):
    """Converts bytes to string.

    Parameters:
    binaryData (bytearray): Buffer which will be converted.

    Returns:
    str: String value.
    """
    return "{0:b}".format(binary_to_integer(binary_data))


def get_dictionary_by_value(dictionary_list, key_name, value):
    """Gets dictionary by given name of the key and value.

    Parameters:
    dictionary_list (object): Dictionary list.
    key_name (object|str): Name of the key
    value (object|str|int): Value

    Returns:
    object|str|int: dictionary
    """
    for dictonary in dictionary_list:
        if dictonary[key_name] == value:
            return dictonary
    return None


def change_buffer_size(buff, start, end=None):
    """Changes buffer size.

    Parameters:
    buff (bytearray): Bytearray which size will be changed.
    start (bytearray): Bytearray's start index.
    start (bytearray): Bytearray's end index. (optional)

    Returns:
    bytearray: New size bytearray
    """
    buffer_array = []
    index = start
    if not end:
        end = len(buff)

    if not isinstance(buff, bytearray):
        raise ValueError('Given argument is not a buffer')

    if start < 0:
        raise ValueError('Wanted buffer start is negative number')

    if len(buff) < end:
        raise ValueError('Buffer length is smaller than wanted buffer end')

    if start > end:
        raise ValueError('Wanted buffer start is larger number than end')

    while index < end:
        buffer_array.append(buff[index])
        index += 1

    return bytearray(buffer_array)


def decode(buff):
    """Decodes any TLV bytearray.

    Parameters:
    buff (bytearray): encoded TLV bytearray

    Returns:
    object: Decoded object
    """
    i = None
    value_identifier = None
    index = 1
    value_length = 0

    if not isinstance(buff, bytearray):
        raise ValueError('Given argument is not a bytearray')

    if len(buff) < 2:
        raise ValueError('Given buffer is too short to store tlv data')

    value_identifier = buff[index]
    index += 1
    i = index
    if (index + (buff[0] >> 5) & 0b1) > 0:
        if buff[i] is None:
            raise ValueError('Given buffer is corrupted (missing data)')

        value_identifier = (value_identifier << 8) + buff[i]
        i += 1

    index = i

    if (buff[0] >> 3) & 0b11 > 0:
        while i < (index + ((buff[0] >> 3) & 0b11)):
            if buff[i] is None:
                raise ValueError('Given buffer is corrupted (missing data)')

            value_length = (value_length << 8) + buff[i]
            i += 1

    else:
        value_length = buff[0] & 0b111
    index = i

    return {
        'type': buff[0] >> 6,
        'identifier': value_identifier,
        'value': change_buffer_size(buff, index, index + value_length),
        'tlvSize': index + value_length
    }


def decode_resource_value(buff, resource):
    """Decodes value of the resource.

    Parameters:
    buff (bytearray): Bytearray which will be decoded
    resource (object): Object which stores resource value's type

    Returns:
    object|str|int|bool: Decoded value in specified type
    """
    if resource['type'] == RESOURCE_TYPE['INTEGER']:
        if not buff:
            return 0
        elif len(buff) == 1:
            return unpack('b', buff)[0]
        elif len(buff) == 2:
            return unpack('>h', buff)[0]
        elif len(buff) == 4:
            return unpack('>i', buff)[0]
        else:
            raise ValueError('Incorrect integer value length', len(buff))

    elif resource['type'] == RESOURCE_TYPE['FLOAT']:
        if len(buff) == 4:
            return unpack('>f', buff)[0]
        elif len(buff) == 8:
            return unpack('>d', buff)[0]
        else:
            raise ValueError('Incorrect float value length', len(buff))

    elif resource['type'] == RESOURCE_TYPE['STRING']:
        return buff.decode('ascii')

    elif resource['type'] == RESOURCE_TYPE['BOOLEAN']:
        return binary_to_bit_string(buff) != '0'

    elif resource['type'] == RESOURCE_TYPE['OPAQUE']:
        return buff

    else:
        raise ValueError('Unrecognised resource type', resource['type'])


def decode_multi_resource_instances(buff, resources):
    """Decodes multiple resource TLV byte array.

    Parameters:
    buff (bytearray): TLV byte array
    resources (object): Object which stores identifier and resource type

    Returns:
    object: Decoded resource.
    """
    decoded_resource_values = []
    decoded_resource_instance = None
    index = 0

    while index < len(buff):
        decoded_resource_instance = decode_resource_instance_value(
            change_buffer_size(buff, index),
            resources
        )
        decoded_resource_values.append(decoded_resource_instance['value'])
        index += decoded_resource_instance['tlvSize']

    return {
        'identifier': resources['identifier'],
        'type': resources['type'],
        'value': decoded_resource_values,
    }


def decode_resource(buff, resource):
    """Decodes resource.

    Parameters:
    buff (bytearray): Resource TLV byte array
    resources (object): Object which stores identifier and resource type

    Returns:
    object: Decoded resource.
    """
    decoded_resource = decode(buff)
    resource_value = None

    if resource['identifier'] != decoded_resource['identifier']:
        raise ValueError(
            'Decoded resource TLV identifier and description identifiers do not match')

    if decoded_resource['type'] == TYPE['RESOURCE']:
        resource_value = decode_resource_value(decoded_resource['value'], resource)
    elif decoded_resource['type'] == TYPE['MULTIPLE_RESOURCE']:
        resource_value = decode_multi_resource_instances(
            decoded_resource['value'], resource)['value']
    else:
        raise ValueError('TLV type is not resource or multiple resource')

    return {
        'identifier': resource['identifier'],
        'type': resource['type'],
        'value': resource_value,
        'tlvSize': decoded_resource['tlvSize']
    }


def encode_resource_value(resource):
    """Encodes value of the resource.

    Parameters:
    resource (object): Object which stores resource value and value's type

    Returns:
    bytearray: Byte array of encoded value
    """
    min_int8 = -0x80
    max_int8 = 0x7f
    min_int16 = -0x8000
    max_int16 = 0x7fff
    min_int32 = -0x80000000
    max_int32 = 0x7fffffff

    buff = None

    if not str(resource['type']).isdigit():
        raise ValueError('Unrecognised type ', resource['type'])

    if resource['type'] == RESOURCE_TYPE['NONE']:
        if not isinstance(resource['value'], int) or isinstance(resource['value'], float):
            raise ValueError('Unrecognised value type ',
                             type(resource['type']))

        return bytearray()

    elif resource['type'] == RESOURCE_TYPE['INTEGER']:
        if not isinstance(resource['value'], numbers.Number):
            raise ValueError('Cannot encode ', type(
                resource['value']), ' as integer')

        if (resource['value'] >= min_int8 and resource['value'] <= max_int8):
            buff = bytearray(pack('>b', resource['value']))
        elif (resource['value'] >= min_int16 and resource['value'] <= max_int16):
            buff = bytearray(pack('>h', resource['value']))
        elif (resource['value'] >= min_int32 and resource['value'] <= max_int32):
            buff = bytearray(pack('>i', resource['value']))
        else:
            raise ValueError('64-bit integers are not supported')

        return buff

    elif resource['type'] == RESOURCE_TYPE['FLOAT']:
        if not isinstance(resource['value'], numbers.Number):
            raise ValueError('Cannot encode ', type(
                resource['value']), ' as float')

        buff = bytearray(pack('>f', resource['value']))
        return buff

    elif resource['type'] == RESOURCE_TYPE['BOOLEAN']:
        if not isinstance(resource['value'], bool):
            raise ValueError('Cannot encode ', type(
                resource['value']), ' as boolean')

        if resource['value']:
            return bytearray([1])
        return bytearray([0])

    elif resource['type'] == RESOURCE_TYPE['STRING']:
        if not isinstance(resource['value'], str):
            raise ValueError('Cannot encode ', type(
                resource['value']), ' as string')

        return bytearray(resource['value'], 'ascii')

    elif resource['type'] == RESOURCE_TYPE['OPAQUE']:
        if not isinstance(resource['value'], bytearray):
            raise ValueError('Cannot encode ', type(
                resource['value']), ' as bytearray')

        return resource['value']

    else:
        raise ValueError('Unrecognised type: ', resource['type'])


def encode(obj):
    """Encodes ant type of instance (Object instance, multiple resources,
    resources instance, resource).

    Parameters:
    obj (object): Object which stores type, identifier and value

    Returns:
    bytearray: Encoded TLV byte array
    """
    identifier_buffer = None
    length_buffer = None
    type_byte = 0

    if not isinstance(obj['value'], bytearray):
        raise ValueError('Encodable object value is not a bytearray')

    if not isinstance(obj['identifier'], numbers.Number):
        raise ValueError('Encodable object identifier is not a number')
    type_byte += obj['type'] << 6

    if obj['identifier'] >= (1 << 8):
        type_byte += 1 << 5
        identifier_buffer = bytearray([
            int(obj['identifier'] / (1 << 8)),
            obj['identifier'] % (1 << 8),
        ])
    else:
        identifier_buffer = bytearray([obj['identifier']])

    if len(obj['value']) >= (1 << 16):
        type_byte += 3 << 3

        length_buffer = bytearray([
            int(len(obj['value']) / (1 << 16)),
            int((int(len(obj['value']) / (1 << 8)) >> (8 * 0)) & 0xFF),
            len(obj['value']) % (1 << 8),
        ])
    elif len(obj['value']) >= (1 << 8):
        type_byte += 2 << 3

        length_buffer = bytearray([
            int(len(obj['value']) / (1 << 8)),
            len(obj['value']) % (1 << 8),
        ])
    elif len(obj['value']) >= (1 << 3):
        type_byte += 1 << 3

        length_buffer = bytearray([len(obj['value'])])
    else:
        type_byte += len(obj['value'])

        length_buffer = bytearray([])

    return bytearray([type_byte]) + identifier_buffer + length_buffer + obj['value']


def encode_resource_instance(resource_instance):
    """Encodes resource instance to TLV byte array.
    resources instance, resource).

    Parameters:
    resource_instance (object): Object which stores resource identifier,
    value and it's type.

    Returns:
    bytearray: Byte array in TLV format
    """
    return encode({
        'type': TYPE['RESOURCE_INSTANCE'],
        'identifier': resource_instance['identifier'],
        'value': encode_resource_value(resource_instance),
    })


def encode_multiple_resources_tlv(resources):
    """Encodes multiple resource values to TLV byte array.

    Parameters:
    resources (object): Object which stores identifier, resource type,
    and multiple values

    Returns:
    bytearray: TLV byte array
    """
    resource_instances_buffers = bytearray()

    for index in range(len(resources['value'])):
        resource_instances_buffers += encode_resource_instance({
            'type': resources['type'],
            'identifier': index,
            'value': resources['value'][index],
        })

    return encode({
        'type': TYPE['MULTIPLE_RESOURCE'],
        'identifier': resources['identifier'],
        'value': resource_instances_buffers,
    })


def encode_resource(resource):
    """Encodes resource to TLV byte array.

    Parameters:
    resource (object): Object which stores resource identifier, type and value.

    Returns:
    bytearray: TLV byte array
    """
    if isinstance(resource['value'], list):
        return encode_multiple_resources_tlv(resource)

    return encode({
        'type': TYPE['RESOURCE'],
        'identifier': resource['identifier'],
        'value': encode_resource_value(resource),
    })


def encode_object_instance(object_instance):
    """Encodes LwM2M object instance to TLV byte array.

    Parameters:
    object_instance (object): LwM2M object instance

    Returns:
    bytearray: TLV byte array
    """
    resources_buffers = bytearray()

    for index in range(len(object_instance['resources'])):
        resources_buffers += encode_resource(object_instance['resources'][index])

    return encode({
        'type': TYPE['OBJECT_INSTANCE'],
        'identifier': object_instance['identifier'],
        'value': resources_buffers,
    })


def encode_object(obj):
    """Encodes LwM2M object to TLV byte array

    Parameters:
    obj (object): LwM2M object

    Returns:
    bytearray: TLV byte array
    """
    object_instances_buffers = bytearray()

    for index in range(len(obj['object_instances'])):
        object_instances_buffers += encode_object_instance(
            obj['object_instances'][index])

    return object_instances_buffers


def decode_resource_instance(buff, resources):
    """Decodes resource instance.

    Parameters:
    buff (bytearray): Resource instance TLV byte array
    resources (object): Object which stores resource identifier and resource type

    Returns:
    object: Object which stores resource identifier,
    tlvSize resource type and value.
    """
    decoded_resource_instance = decode(buff)

    if decoded_resource_instance['type'] != TYPE['RESOURCE_INSTANCE']:
        raise ValueError('Decoded resource TLV type is not resource instance')

    return {
        'type': resources['type'],
        'identifier': decoded_resource_instance['identifier'],
        'value': decode_resource_value(decoded_resource_instance['value'], resources),
        'tlvSize': decoded_resource_instance['tlvSize'],
    }


def decode_resource_instance_value(buff, resource_instance):
    """Decodes resource instance value

    Parameters:
    buff (bytearray): Resource instance TLV byte array
    resource_instance (object): Object which stores resource type

    Returns:
    object: Decoded resource value
    """
    decoded_resource_instance = decode(buff)

    if decoded_resource_instance['type'] != TYPE['RESOURCE_INSTANCE']:
        raise ValueError('Decoded resource TLV type is not resource instance')

    return {
        'value': decode_resource_value(decoded_resource_instance['value'], resource_instance),
        'tlvSize': decoded_resource_instance['tlvSize'],
    }


def decode_object_instance(buff, object_instance):
    """Decodes object instance from TLV byte array.

    Parameters:
    buff (bytearray): TLV byte array
    object_instance (object): Object which stores object instance identifier and resources

    Returns:
    object:  Decoded object instance
    """
    decoded_object_instance = decode(buff)
    decoded_resources = []
    remaining_buffer = None
    resource_identifier = None
    resource_description = None
    decoded_resource = None
    index = 0

    while index < len(decoded_object_instance['value']):
        remaining_buffer = change_buffer_size(
            decoded_object_instance['value'], index, len(decoded_object_instance['value']))
        resource_identifier = decode(remaining_buffer)['identifier']

        resource_description = get_dictionary_by_value(
            object_instance['resources'], 'identifier', resource_identifier)

        if resource_description is None:
            raise ValueError('No resource description found (x/',
                             object_instance['identifier'], '/', resource_identifier, ')')

        decoded_resource = decode_resource(remaining_buffer, resource_description)
        decoded_resources.append(decoded_resource)
        index += decoded_resource['tlvSize']

    return {
        'identifier': object_instance['identifier'],
        'resources': decoded_resources,
    }


def decode_object(buff, obj):
    """Decodes LwM2M object to TLV byte array.

    Parameters:
    buff (bytearray): TLV byte array
    obj (object): Object which stores object instances with their resources

    Returns:
    object:  Decoded object
    """
    decoded_object_instances = []
    remaining_buffer = None
    object_instance_identifier = None
    object_instance_description = None
    decoded_object_instance = None
    index = 0

    while index < len(buff):
        remaining_buffer = change_buffer_size(buff, index, len(buff))
        object_instance_identifier = decode(remaining_buffer)['identifier']

        object_instance_description = get_dictionary_by_value(
            obj['object_instances'], 'identifier', object_instance_identifier)

        if object_instance_description is None:
            raise ValueError('No object instance description found (',
                             obj['identifier'], '/', object_instance_identifier, ')')

        decoded_object_instance = decode_object_instance(
            remaining_buffer, object_instance_description)
        decoded_object_instances.append(decoded_object_instance)
        break

    return {
        'identifier': obj['identifier'],
        'object_instances': decoded_object_instances,
    }
