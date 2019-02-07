import unittest
import sys

sys.path.append('../')
from tlv import *

class TestEncodeResourceValue(unittest.TestCase):
	def encode_exception_type_unrecognizable(self):
		res = {
			'type': RESOURCE_TYPE['UNRECOGNIZABLE'],
			'value': 'NAN'
		}
		with self.assertRaises(Exception):
			encoded = encodeResourceValue(res)
	
	def test_encode_value_empty_buffer_return(self):
		res = {
			'type': RESOURCE_TYPE['NONE'],
			'value': 0x80000000
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray())
		
	def test_encode_value_integer_0(self):
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
			'value': 0
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0x00]))
		
	def test_encode_value_integer_1(self):
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
			'value': 1
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0x01]))
		
	def test_encode_value_integer__minus_1(self):
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
			'value': -1
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0xff]))
		
	def test_encode_value_integer_2_pow_15(self):
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
			'value': 32767
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0x7f, 0xff]))
		
	def test_encode_value_integer_minus_2_pow_15(self):
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
			'value': -0x8000
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0x80, 0x00]))
		
	def test_encode_value_integer_2_pow_31(self):
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
			'value': 0x7fffffff
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0x7f, 0xff, 0xff, 0xff]))
		
	def test_encode_value_integer_minus_2_pow_31(self):
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
			'value': -0x80000000
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0x80, 0x00, 0x00, 0x00]))
		
	def test_encode_value_float_1_point_23(self):
		res = {
			'type': RESOURCE_TYPE['FLOAT'],
			'value': 1.23
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0x3f, 0x9d, 0x70, 0xa4]))
		
	def test_encode_value_resource_type_and_value_type_not_match_exception(self):
		res = {
			'type': RESOURCE_TYPE['FLOAT'],
			'value': 'NAN'
		}
		with self.assertRaises(Exception):
			encoded = encodeResourceValue(res)
			
	def test_encode_exception_undefined_type(self):
		res = {
			'type': 99,
			'value': 'NAN'
		}
		with self.assertRaises(Exception):
			encoded = encodeResourceValue(res)
		
	def test_encode_value_boolean(self):
		res = {
			'type': RESOURCE_TYPE['BOOLEAN'],
			'value': True
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0x01]))
		
	def test_encode_value_boolean_type_value_dont_match_exception(self):
		res = {
			'type': RESOURCE_TYPE['BOOLEAN'],
			'value': "NOT BOOLEAN"
		}
		with self.assertRaises(Exception):
			encoded = encodeResourceValue(res)
			
	def test_encode_value_string(self):
		res = {
			'type': RESOURCE_TYPE['STRING'],
			'value': 'text'
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == bytearray([0x74, 0x65, 0x78, 0x74]))
		
	def test_encode_value_string_type_value_dont_match_exception(self):
		res = {
			'type': RESOURCE_TYPE['STRING'],
			'value': 1324
		}
		with self.assertRaises(Exception):
			encoded = encodeResourceValue(res)
			
	def test_encode_value_opaque_pass_bytes(self):
		buff = bytearray([0x74, 0x65, 0x78, 0x74])
		res = {
			'type': RESOURCE_TYPE['OPAQUE'],
			'value': buff
		}
		encoded = encodeResourceValue(res)
		self.assertTrue(encoded == buff)
		
	def test_encode_value_opaque_type_value_dont_match_exception(self):
		res = {
			'type': RESOURCE_TYPE['OPAQUE'],
			'value': 'NOT OPAQUE'
		}
		with self.assertRaises(Exception):
			encoded = encodeResourceValue(res)
			
class TestDecodeResourceValue(unittest.TestCase):
	def test_return_0_when_empty_buffer_given(self):
		buff = bytearray()
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
		}
		decoded = decodeResourceValue(buff, res)
		self.assertTrue(decoded == 0)
		
	def test_decode_8_bit_integer(self):
		buff = bytearray([0x01])
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
		}
		decoded = decodeResourceValue(buff, res)
		self.assertTrue(decoded == 1)
		
	def test_decode_16_bit_integer(self):
		buff = bytearray([0x00, 0x80])
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
		}
		decoded = decodeResourceValue(buff, res)
		self.assertTrue(decoded == 128)
		
	def test_decode_32_bit_integer(self):
		buff = bytearray([0x7f, 0xff, 0xff, 0xff])
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
		}
		decoded = decodeResourceValue(buff, res)
		self.assertTrue(decoded == 0x7FFFFFFF)
		
	def test_exception_integer_wrong_buffer_length(self):
		buff = bytearray([0x7f, 0xff, 0xff])
		res = {
			'type': RESOURCE_TYPE['INTEGER'],
		}
		with self.assertRaises(Exception):
			decoded = decodeResourceValue(buff, res)
			
	def test_decode_float(self):
		buff = bytearray([0x3f, 0x9d, 0x70, 0xa4])
		res = {
			'type': RESOURCE_TYPE['FLOAT'],
		}
		decoded = decodeResourceValue(buff, res)
		self.assertTrue(round(decoded, 7) == 1.23)
		
	def test_decode_double(self):
		buff = bytearray([0x3f, 0xf3, 0xae, 0x14, 0x7a, 0xe1, 0x47, 0xae])
		res = {
			'type': RESOURCE_TYPE['FLOAT'],
		}
		decoded = decodeResourceValue(buff, res)
		self.assertTrue(decoded == 1.23)
		
	def test_exception_float_or_double_wrong_buffer_length(self):
		buff = bytearray([0x7f, 0xff, 0xff])
		res = {
			'type': RESOURCE_TYPE['FLOAT'],
		}
		with self.assertRaises(Exception):
			decoded = decodeResourceValue(buff, res)
			
	def test_exception_wrong_type(self):
		buff = bytearray([0x7f, 0xff, 0xff])
		res = {
			'type': 99,
		}
		with self.assertRaises(Exception):
			decoded = decodeResourceValue(buff, res)
			
	def test_decode_string(self):
		buff = bytearray([0x74, 0x65, 0x78, 0x74])
		res = {
			'type': RESOURCE_TYPE['STRING'],
		}
		decoded = decodeResourceValue(buff, res)
		self.assertTrue(decoded == 'text')
		
	def test_decode_boolean(self):
		buff = bytearray([0x01])
		res = {
			'type': RESOURCE_TYPE['BOOLEAN'],
		}
		decoded = decodeResourceValue(buff, res)
		self.assertTrue(decoded == True)
	
	def test_decode_opaque_pass_buffer(self):
		buff = bytearray([0x02])
		res = {
			'type': RESOURCE_TYPE['OPAQUE'],
		}
		decoded = decodeResourceValue(buff, res)
		self.assertTrue(decoded == buff)
		
class TestEncode(unittest.TestCase):
	def test_encode_resource_16_bit_value(self):
		res = {
		    'identifier': 5850,
			'type': TYPE['RESOURCE'],
			'value': bytearray(256)
		}
		encoded = encode(res)
		buff = bytearray([0xF0, 0x16, 0xda, 0x01, 0x00]) + bytearray(256)
		self.assertTrue(encoded == buff)
		
	def test_encode_resource_24_bit_value(self):
		res = {
		    'identifier': 5850,
			'type': TYPE['RESOURCE'],
			'value': bytearray(0x3987D)
		}
		encoded = encode(res)
		buff = bytearray([0xF8, 0x16, 0xda, 0x03, 0x98, 0x7d]) + bytearray(0x3987D)
		self.assertTrue(encoded == buff)
		
	def test_exception_value_not_bytearray(self):
		res = {
		    'identifier': 5850,
			'type': TYPE['RESOURCE'],
			'value': 123
		}
		with self.assertRaises(Exception):
			encoded = encode(res)
			
	def test_exception_identifier_not_a_number(self):
		res = {
		    'identifier': 'NAN',
			'type': TYPE['RESOURCE'],
			'value': bytearray(256)
		}
		with self.assertRaises(Exception):
			encoded = encode(res)
			
class TestDecode(unittest.TestCase):
	def test_exception_argument_not_a_bytearray(self):
		buff= 123
		with self.assertRaises(Exception):
			encoded = decode(buff)
			
class TestDecodeResource(unittest.TestCase):
	def test_decode_one_resource(self):
		buff = bytearray([0xe1, 0x16, 0xda, 0x01])
		res = {
		    'identifier': 5850,
			'type': RESOURCE_TYPE['BOOLEAN'],
		}
		decoded = decodeResource(buff, res)
		self.assertTrue(decoded['identifier'] == 5850)
		self.assertTrue(decoded['type'] == 1)
		self.assertTrue(decoded['value'] == True)
		self.assertTrue(decoded['tlvSize'] == 4)

	def test_decode_multiple_resource(self):
		buff = bytearray([0xa6, 0x16, 0xda, 0x41, 0x00, 0x01, 0x41, 0x01, 0x00])
		res = {
		    'identifier': 5850,
			'type': RESOURCE_TYPE['BOOLEAN'],
		}
		decoded = decodeResource(buff, res)
		self.assertTrue(decoded['identifier'] == 5850)
		self.assertTrue(decoded['type'] == 1)
		self.assertTrue(decoded['value'] == [True, False])
		self.assertTrue(decoded['tlvSize'] == 9)

class TestEncodeResourceInstance(unittest.TestCase):
	def test_encode_resource_instance(self):
		res = {
			'identifier': 5850,
			'type': RESOURCE_TYPE['BOOLEAN'],
			'value': True
		}
		encoded = encodeResourceInstance(res)
		buff = bytearray([0x61, 0x16, 0xda, 0x01])
		self.assertTrue(encoded == buff)

class TestDecodeResourceInstance(unittest.TestCase):
	def test_decode_resource_instance(self):
		buff = bytearray([0x61, 0x16, 0xda, 0x01])
		res = {
		    'identifier': 5850,
			'type': RESOURCE_TYPE['BOOLEAN'],
		}
		decoded = decodeResourceInstance(buff, res)
		self.assertTrue(decoded['identifier'] == 5850)
		self.assertTrue(decoded['type'] == 1)
		self.assertTrue(decoded['value'] == True)
		self.assertTrue(decoded['tlvSize'] == 4)

class TestEncodeObject(unittest.TestCase):
	def test_encode_object(self):
		obj = {
			'identifier': 3305,
			'objectInstances': [{
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
		encoded = encodeObject(obj)
		buff = bytearray([0x08, 0x00, 0x1c,
        0xe4, 0x16, 0xa8, 0x00, 0x00, 0x00, 0x00,
        0xe4, 0x16, 0xad, 0x3f, 0x80, 0x00, 0x00,
        0xe4, 0x16, 0xb2, 0x3f, 0x9d, 0x70, 0xa4,
        0xe4, 0x16, 0xb7, 0x44, 0x79, 0xff, 0x5c])
		self.assertTrue(encoded == buff)
		

class TestDecodeObject(unittest.TestCase):
	def test_decode_object(self):
		buff = bytearray([0x08, 0x00, 0x1c,
        0xe4, 0x16, 0xa8, 0x00, 0x00, 0x00, 0x00,
        0xe4, 0x16, 0xad, 0x3f, 0x9d, 0x70, 0xa4,
        0xe4, 0x16, 0xb2, 0x44, 0x79, 0xff, 0x5c,
        0xe4, 0x16, 0xb7, 0x3f, 0x80, 0x00, 0x00])
		obj = {
			'identifier': 3305,
			'objectInstances': [{
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
		decoded = decodeObject(buff, obj)
		values = []
		for resource in decoded['objectInstances'][0]['resources']:
			values.append(resource['value']);
		self.assertTrue(round(values[0],4) == 0)
		self.assertTrue(round(values[1],4) == 1.23)
		self.assertTrue(round(values[2],4) == 999.99)
		self.assertTrue(round(values[3],4) == 1)


if __name__ == '__main__':
	unittest.main()
