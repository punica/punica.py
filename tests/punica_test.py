import responses
import requests
import unittest
import sys
from rest_response import resp

sys.path.append('../')
from punica import Service
from punica import Device

service = Service()
url = 'http://localhost:8888'
deviceName = 'threeSeven'
path = '/3312/0/5850'


class TestServiceMethods(unittest.TestCase):
	@responses.activate
	def test_pull_notification_return(self):
		responses.add(responses.GET, url + '/notification/pull',
			json= resp['oneAsyncResponse'], status=200)

		response = service.pullNotification();
		self.assertTrue('registrations' in response.keys())
		self.assertTrue('reg-updates' in response.keys())
		self.assertTrue('de-registrations' in response.keys())
		self.assertTrue('async-responses' in response.keys())

	@responses.activate
	def test_pull_notification_wrong_status(self):
		responses.add(responses.GET, url + '/notification/pull',
			status=404)

		response= None
		with self.assertRaisesRegexp(requests.HTTPError, '404'):
			response = service.pullNotification()

	def test_pull_notification_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.pullNotification()

	@responses.activate
	def test_get_devices_return(self):
		responses.add(responses.GET, url + '/endpoints',
			json= resp['endpoints'], status=200)

		response = service.getDevices();
		self.assertTrue('name' in response[0].keys())
		self.assertTrue('type' in response[0].keys())
		self.assertTrue('status' in response[0].keys())
		self.assertTrue('q' in response[0].keys())

	@responses.activate
	def test_get_devices_wrong_status(self):
		responses.add(responses.GET, url + '/endpoints',
			status=404)

		response= None
		with self.assertRaisesRegexp(requests.HTTPError, '404'):
			response = service.getDevices()

	def test_get_devices_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.getDevices()
	
	@responses.activate
	def test_get_version_return(self):
		responses.add(responses.GET, url + '/version',
			json= resp['version'], status=200)

		response = service.getVersion();
		self.assertEqual(str(response), '1.0.0')

	def test_get_version_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.getDevices()

if __name__ == '__main__':
	unittest.main()
