""" Tests for LwM2M TLV encoding, decoding methods """
import unittest
from tlv import RESOURCE_TYPE, TYPE, encode_resource_value, \
	decode_resource_value, encode, decode, encode_resource, \
	decode_resource, encode_resource_instance, \
	decode_resource_instance, encode_object, \
	decode_object


class TestEncodeResourceValue(unittest.TestCase):
    """
    Tests for encode_resource_value method
    """

    def test_type_unrecognizable(self):
        """
        should raise an error if resource type is not recognized or supported
        """
        res = {
            'type': RESOURCE_TYPE.get("UNRECOGNIZABLE"),
            'value': 'NAN'
        }
        with self.assertRaises(Exception):
            encode_resource_value(res)

    def test_encode_value_empty_buff(self):
        """
        should return empty bytearray if resource type is set to none
        """
        res = {
            'type': RESOURCE_TYPE['NONE'],
            'value': 0x80000000
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray())

    def test_encode_value_integer_0(self):
        """
        should encode integer (0)
        """
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
            'value': 0
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x00]))

    def test_encode_value_integer_1(self):
        """
        should encode integer (1)
        """
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
            'value': 1
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x01]))

    def test_encode_int__minus_1(self):
        """
        should encode integer (-1)
        """
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
            'value': -1
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0xff]))

    def test_encode_int_2_pow_15_min_1(self):
        """
        should encode integer (2^15-1)
        """
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
            'value': 32767
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x7f, 0xff]))

    def test_encode_int_2_pow_15(self):
        """
        should encode integer (2^15)
        """
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
            'value': 0x8000
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x00, 0x00, 0x80, 0x00]))

    def test_encode_int_minus_2_pow_15(self):
        """
        should encode integer (-2^15)
        """
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
            'value': -0x8000
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x80, 0x00]))

    def test_encode_int_2_pow_31_min_1(self):
        """
        should encode integer (2^31 -1)
        """
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
            'value': 0x7fffffff
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x7f, 0xff, 0xff, 0xff]))

    def test_encode_int_minus_2_pow_31(self):
        """
        should encode integer (0)
        """
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
            'value': -0x80000000
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x80, 0x00, 0x00, 0x00]))

    def test_encode_float_1_point_23(self):
        """
        should encode float (1.23)
        """
        res = {
            'type': RESOURCE_TYPE['FLOAT'],
            'value': 1.23
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x3f, 0x9d, 0x70, 0xa4]))

    def test_encode_type_not_match(self):
        """
        should throw an error if resource type
        is set to float and value is not a number'
        """
        res = {
            'type': RESOURCE_TYPE['FLOAT'],
            'value': 'NAN'
        }
        with self.assertRaises(Exception):
            encode_resource_value(res)

    def test_encode_undefined_type(self):
        """
        should raise an error if resource type is a number
        which is not defined in resource type dictionary
        """
        res = {
            'type': 99,
            'value': 'NAN'
        }
        with self.assertRaises(Exception):
            encode_resource_value(res)

    def test_encode_value_boolean(self):
        """
        should encode boolean (true)
        """
        res = {
            'type': RESOURCE_TYPE['BOOLEAN'],
            'value': True
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x01]))

    def test_encode_bool_type_not_match(self):
        """
        should raise an error if resource type is set
        to boolean and value is not a boolean
        """
        res = {
            'type': RESOURCE_TYPE['BOOLEAN'],
            'value': "NOT BOOLEAN"
        }
        with self.assertRaises(Exception):
            encode_resource_value(res)

    def test_encode_value_string(self):
        """
        should encode string (text)
        """
        res = {
            'type': RESOURCE_TYPE['STRING'],
            'value': 'text'
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == bytearray([0x74, 0x65, 0x78, 0x74]))

    def test_encode_str_type_not_match(self):
        """
        should throw an error if resource type is set
        to string and value is not a string
        """
        res = {
            'type': RESOURCE_TYPE['STRING'],
            'value': 1324
        }
        with self.assertRaises(Exception):
            encode_resource_value(res)

    def test_encode_opaque_pass_bytes(self):
        """
        should handle opaque (bytearray <0x74, 0x65, 0x78, 0x74>)
        """
        buff = bytearray([0x74, 0x65, 0x78, 0x74])
        res = {
            'type': RESOURCE_TYPE['OPAQUE'],
            'value': buff
        }
        encoded = encode_resource_value(res)
        self.assertTrue(encoded == buff)

    def test_opaque_type_not_match(self):
        """
        should throw an error if resource type is set
        to opaque and value is not a bytearray
        """
        res = {
            'type': RESOURCE_TYPE['OPAQUE'],
            'value': 'NOT OPAQUE'
        }
        with self.assertRaises(Exception):
            encode_resource_value(res)


class TestDecodeResourceValue(unittest.TestCase):
    """
    Tests for decode_resource_value method
    """

    def test_return_0_empty_buff_given(self):
        """
        return 0 if given buffer is empty
        """
        buff = bytearray()
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
        }
        decoded = decode_resource_value(buff, res)
        self.assertTrue(decoded == 0)

    def test_decode_8_bit_integer(self):
        """
        should decode buffer to 8 bit integer
        """
        buff = bytearray([0x01])
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
        }
        decoded = decode_resource_value(buff, res)
        self.assertTrue(decoded == 1)

    def test_decode_16_bit_integer(self):
        """
        should decode buffer to 16 bit integer
        """
        buff = bytearray([0x00, 0x80])
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
        }
        decoded = decode_resource_value(buff, res)
        self.assertTrue(decoded == 128)

    def test_decode_32_bit_integer(self):
        """
        should decode buffer to 32 bit integer
        """
        buff = bytearray([0x7f, 0xff, 0xff, 0xff])
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
        }
        decoded = decode_resource_value(buff, res)
        self.assertTrue(decoded == 0x7FFFFFFF)

    def test_integer_wrong_buff_length(self):
        """
        should raise an error if given buffer length
        does not meet 8, 16, 32 bit integer
        """
        buff = bytearray([0x7f, 0xff, 0xff])
        res = {
            'type': RESOURCE_TYPE['INTEGER'],
        }
        with self.assertRaises(Exception):
            decode_resource_value(buff, res)

    def test_decode_float(self):
        """
        should decode buffer to float
        """
        buff = bytearray([0x3f, 0x9d, 0x70, 0xa4])
        res = {
            'type': RESOURCE_TYPE['FLOAT'],
        }
        decoded = decode_resource_value(buff, res)
        self.assertTrue(round(decoded, 7) == 1.23)

    def test_decode_double(self):
        """
        should decode buffer to double
        """
        buff = bytearray([0x3f, 0xf3, 0xae, 0x14, 0x7a, 0xe1, 0x47, 0xae])
        res = {
            'type': RESOURCE_TYPE['FLOAT'],
        }
        decoded = decode_resource_value(buff, res)
        self.assertTrue(decoded == 1.23)

    def test_float_double_wrong_length(self):
        """
        should raise an error if given buffer length
        does not meet float or double
        """
        buff = bytearray([0x7f, 0xff, 0xff])
        res = {
            'type': RESOURCE_TYPE['FLOAT'],
        }
        with self.assertRaises(Exception):
            decode_resource_value(buff, res)

    def test_exception_wrong_type(self):
        """
        should throw an error if resource type is a number
        which is not defined in resource type dictionary
        """
        buff = bytearray([0x7f, 0xff, 0xff])
        res = {
            'type': 99,
        }
        with self.assertRaises(Exception):
            decode_resource_value(buff, res)

    def test_decode_string(self):
        """
        should decode buffer to string
        """
        buff = bytearray([0x74, 0x65, 0x78, 0x74])
        res = {
            'type': RESOURCE_TYPE['STRING'],
        }
        decoded = decode_resource_value(buff, res)
        self.assertTrue(decoded == 'text')

    def test_decode_boolean(self):
        """
        should decode buffer to boolean
        """
        buff = bytearray([0x01])
        res = {
            'type': RESOURCE_TYPE['BOOLEAN'],
        }
        decoded = decode_resource_value(buff, res)
        self.assertTrue(decoded)

    def test_decode_opaque_pass_buffer(self):
        """
        should handle opaque resource type and return bytearray
        """
        buff = bytearray([0x02])
        res = {
            'type': RESOURCE_TYPE['OPAQUE'],
        }
        decoded = decode_resource_value(buff, res)
        self.assertTrue(decoded == buff)


class TestEncode(unittest.TestCase):
    """
    Tests for encode method
    """

    def test_encode_resource_16_bit(self):
        """
        should encode resource with 16 bit value length and return a bytearray
        """
        res = {
            'identifier': 5850,
            'type': TYPE['RESOURCE'],
            'value': bytearray(256)
        }
        encoded = encode(res)
        buff = bytearray([0xF0, 0x16, 0xda, 0x01, 0x00]) + bytearray(256)
        self.assertTrue(encoded == buff)

    def test_encode_resource_24_bit(self):
        """
        should encode resource with 24 bit value length and return a bytearray
        """
        res = {
            'identifier': 5850,
            'type': TYPE['RESOURCE'],
            'value': bytearray(0x3987D)
        }
        encoded = encode(res)
        buff = bytearray([0xF8, 0x16, 0xda, 0x03, 0x98, 0x7d]
                        ) + bytearray(0x3987D)
        self.assertTrue(encoded == buff)

    def test_value_not_bytearray(self):
        """
        should raise an error if given value is not a buffer
        """
        res = {
            'identifier': 5850,
            'type': TYPE['RESOURCE'],
            'value': 123
        }
        with self.assertRaises(Exception):
            encode(res)

    def test_identifier_not_a_number(self):
        """
        should raise an error if given identifier is not a number
        """
        res = {
            'identifier': 'NAN',
            'type': TYPE['RESOURCE'],
            'value': bytearray(256)
        }
        with self.assertRaises(Exception):
            encode(res)


class TestDecode(unittest.TestCase):
    """
    Tests for decode method
    """

    def test_argument_not_a_bytearray(self):
        """
        should throw an error if given value is not a bytearray
        """
        buff = 123
        with self.assertRaises(Exception):
            decode(buff)


class TestEncodeResource(unittest.TestCase):
    """
    Tests for encode_resource method
    """

    def test_encode_resource(self):
        """
        should encode resource and return a bytearray
        """
        res = {
            'identifier': 5850,
            'type': RESOURCE_TYPE['BOOLEAN'],
            'value': True
        }
        encoded = encode_resource(res)
        buff = bytearray([0xe1, 0x16, 0xda, 0x01])
        self.assertTrue(encoded == buff)

    def test_encode_multi_value(self):
        """
        should encode multiple resources instance and return a bytearray
        """
        res = {
            'identifier': 5850,
            'type': RESOURCE_TYPE['BOOLEAN'],
            'value': [True, False]
        }
        encoded = encode_resource(res)
        buff = bytearray(
            [0xa6, 0x16, 0xda, 0x41, 0x00, 0x01, 0x41, 0x01, 0x00])
        self.assertTrue(encoded == buff)


class TestDecodeResource(unittest.TestCase):
    """
    Tests for decode_resource method
    """

    def test_decode_one_resource(self):
        """
        should decode resource and return its
        identifier, type, value, tlv size
        """
        buff = bytearray([0xe1, 0x16, 0xda, 0x01])
        res = {
            'identifier': 5850,
            'type': RESOURCE_TYPE['BOOLEAN'],
        }
        decoded = decode_resource(buff, res)
        self.assertTrue(decoded['identifier'] == 5850)
        self.assertTrue(decoded['type'] == 1)
        self.assertTrue(decoded['value'])
        self.assertTrue(decoded['tlvSize'] == 4)

    def test_decode_multiple_resource(self):
        """
        should decode multiple resources and return
        its identifier, type, value, tlv size
        """
        buff = bytearray(
            [0xa6, 0x16, 0xda, 0x41, 0x00, 0x01, 0x41, 0x01, 0x00])
        res = {
            'identifier': 5850,
            'type': RESOURCE_TYPE['BOOLEAN'],
        }
        decoded = decode_resource(buff, res)
        self.assertTrue(decoded['identifier'] == 5850)
        self.assertTrue(decoded['type'] == 1)
        self.assertTrue(decoded['value'] == [True, False])
        self.assertTrue(decoded['tlvSize'] == 9)


class TestEncodeResourceInstance(unittest.TestCase):
    """
    Tests for encode_resource_instance method
    """

    def test_encode_resource_instance(self):
        """
        should encode resource instance and return a bytearray
        """
        res = {
            'identifier': 5850,
            'type': RESOURCE_TYPE['BOOLEAN'],
            'value': True
        }
        encoded = encode_resource_instance(res)
        buff = bytearray([0x61, 0x16, 0xda, 0x01])
        self.assertTrue(encoded == buff)


class TestDecodeResourceInstance(unittest.TestCase):
    """
    Tests for decode_resource_instance method
    """

    def test_decode_resource_instance(self):
        """
        should decode resource instance
        """
        buff = bytearray([0x61, 0x16, 0xda, 0x01])
        res = {
            'identifier': 5850,
            'type': RESOURCE_TYPE['BOOLEAN'],
        }
        decoded = decode_resource_instance(buff, res)
        self.assertTrue(decoded['identifier'] == 5850)
        self.assertTrue(decoded['type'] == 1)
        self.assertTrue(decoded['value'])
        self.assertTrue(decoded['tlvSize'] == 4)


class TestEncodeObject(unittest.TestCase):
    """
    Tests for encode_object method
    """

    def test_encode_object(self):
        """
        should encode object with its instaces and resources
        """
        obj = {
            'identifier': 3305,
            'object_instances': [{
                'identifier': 0,
                'resources': [
                    {
                        'identifier': 5800,
                        'type': RESOURCE_TYPE['FLOAT'],
                        'value': 0
                    },
                    {
                        'identifier': 5805,
                        'type': RESOURCE_TYPE['FLOAT'],
                        'value': 1
                    },
                    {
                        'identifier': 5810,
                        'type': RESOURCE_TYPE['FLOAT'],
                        'value': 1.23
                    },
                    {
                        'identifier': 5815,
                        'type': RESOURCE_TYPE['FLOAT'],
                        'value': 999.99
                    },
                ]
            }]
        }
        encoded = encode_object(obj)
        buff = bytearray([0x08, 0x00, 0x1c,
                          0xe4, 0x16, 0xa8, 0x00, 0x00, 0x00, 0x00,
                          0xe4, 0x16, 0xad, 0x3f, 0x80, 0x00, 0x00,
                          0xe4, 0x16, 0xb2, 0x3f, 0x9d, 0x70, 0xa4,
                          0xe4, 0x16, 0xb7, 0x44, 0x79, 0xff, 0x5c])
        self.assertTrue(encoded == buff)


class TestDecodeObject(unittest.TestCase):
    """
    Tests for decode_object method
    """

    def test_decode_object(self):
        """
        should decode object with its instaces and resources
        """
        buff = bytearray([0x08, 0x00, 0x1c,
                          0xe4, 0x16, 0xa8, 0x00, 0x00, 0x00, 0x00,
                          0xe4, 0x16, 0xad, 0x3f, 0x9d, 0x70, 0xa4,
                          0xe4, 0x16, 0xb2, 0x44, 0x79, 0xff, 0x5c,
                          0xe4, 0x16, 0xb7, 0x3f, 0x80, 0x00, 0x00])
        obj = {
            'identifier': 3305,
            'object_instances': [{
                'identifier': 0,
                'resources': [
                    {
                        'identifier': 5800,
                        'type': RESOURCE_TYPE['FLOAT'],
                    },
                    {
                        'identifier': 5805,
                        'type': RESOURCE_TYPE['FLOAT'],
                    },
                    {
                        'identifier': 5810,
                        'type': RESOURCE_TYPE['FLOAT'],
                    },
                    {
                        'identifier': 5815,
                        'type': RESOURCE_TYPE['FLOAT'],
                    },
                ]
            }]
        }
        decoded = decode_object(buff, obj)
        values = []
        for resource in decoded['object_instances'][0]['resources']:
            values.append(resource['value'])
        self.assertTrue(round(values[0], 4) == 0)
        self.assertTrue(round(values[1], 4) == 1.23)
        self.assertTrue(round(values[2], 4) == 999.99)
        self.assertTrue(round(values[3], 4) == 1)


if __name__ == '__main__':
    unittest.main()
