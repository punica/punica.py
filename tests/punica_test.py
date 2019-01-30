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
tlvBuffer = bytearray([0xe4, 0x16, 0x44, 0x00, 0x00, 0x00, 0x01])
device = Device(service, deviceName)

class TestServiceMethods(unittest.TestCase):
	#-----------------------pullNotification----------------------------
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

	#--------------------------getDevices------------------------------
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

	#-------------------------getVersion--------------------------------
	@responses.activate
	def test_get_version_return(self):
		responses.add(responses.GET, url + '/version',
			json= resp['version'], status=200)

		response = service.getVersion();
		self.assertEqual(response, '1.0.0')

	def test_get_version_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.getDevices()

	#--------------------------authenticate----------------------------
	@responses.activate
	def test_authenticate_return(self):
		responses.add(responses.POST, url + '/authenticate',
			json= resp['authentication'], status=201)

		response = service.authenticate();
		self.assertTrue('access_token' in response.keys())
		self.assertTrue('expires_in' in response.keys())

	@responses.activate
	def test_authenticate_wrong_status(self):
		responses.add(responses.POST, url + '/authenticate',
			status=400)

		response= None
		with self.assertRaisesRegexp(requests.HTTPError, '400'):
			response = service.authenticate()

	def test_authenticate_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.authenticate()

	#------------------registerNotificationCallback---------------------
	@responses.activate
	def test_register_notification_callback_return(self):
		responses.add(responses.PUT, url + '/notification/callback',
			json= resp['registerCallback'], status=204)

		response = service.registerNotificationCallback();
		self.assertTrue(isinstance(response, object))
		self.assertTrue(len(response) == 0)

	@responses.activate
	def test_register_notification_callback_wrong_status(self):
		responses.add(responses.PUT, url + '/notification/callback',
			status=404)

		response= None
		with self.assertRaisesRegexp(requests.HTTPError, '404'):
			response = service.registerNotificationCallback()

	def test_register_notification_callback_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.registerNotificationCallback()

	#----------------------deleteNotificationCallback-------------------
	@responses.activate
	def test_delete_notification_callback_wrong_status(self):
		responses.add(responses.DELETE, url + '/notification/callback',
			status=204)

		response = service.deleteNotificationCallback()
		self.assertTrue(response == 204)


	def test_delete_notification_callback_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.deleteNotificationCallback()

	#------------------------get---------------------------
	@responses.activate
	def test_get_return(self):
		responses.add(responses.GET, url + '/endpoints/' + deviceName + path,
			json= resp['readRequest'], status=202)


		response = service.get('/endpoints/' + deviceName + path)
		self.assertTrue('async-response-id' in response.json().keys())

	@responses.activate
	def test_get_after_authentication(self):
		responses.add(responses.POST, url + '/authenticate',
			json= resp['authentication'], status=201)
		responses.add(responses.GET, url + '/endpoints/' + deviceName + path,
			json= resp['readRequest'], status=202)
		responses.add(responses.GET, url + '/notification/pull',
			json= resp['notifications'], status=200)
		opts = {
		 'authentication' : True,
		 'username': 'admin',
		 'password': 'not-same-as-name',
		 'interval': 123456
		}
		service.start(opts)
		response = service.get('/endpoints/' + deviceName + path)
		self.assertTrue(responses.calls[1].request.headers['Authorization'].find(resp['authentication']['access_token']) != -1)
		service.stop()

	def test_get_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.get('/endpoints/' + deviceName + path)

	#------------------------put---------------------------
	@responses.activate
	def test_put_return(self):
		responses.add(responses.PUT, url + '/endpoints/' + deviceName + path,
			json= resp['writeRequest'], status=202)


		response = service.put('/endpoints/' + deviceName + path, tlvBuffer)
		self.assertTrue('async-response-id' in response.json().keys())


	@responses.activate
	def test_put_after_authentication(self):
		responses.add(responses.POST, url + '/authenticate',
			json= resp['authentication'], status=201)
		responses.add(responses.PUT, url + '/endpoints/' + deviceName + path,
			json= resp['writeRequest'], status=202)
		responses.add(responses.GET, url + '/notification/pull',
			json= resp['notifications'], status=200)
		opts = {
		 'authentication' : True,
		 'username': 'admin',
		 'password': 'not-same-as-name',
		 'interval': 123456
		}
		service.start(opts)
		response = service.put('/endpoints/' + deviceName + path, tlvBuffer)
		self.assertTrue(responses.calls[1].request.headers['Authorization'].find(resp['authentication']['access_token']) != -1)
		service.stop()


	def test_put_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.put('/endpoints/'+deviceName+'/'+path, tlvBuffer)

	#------------------------post--------------------------
	@responses.activate
	def test_post_return(self):
		responses.add(responses.POST, url + '/endpoints/' + deviceName + path,
			json= resp['executeRequest'], status=202)


		response = service.post('/endpoints/' + deviceName + path)
		self.assertTrue('async-response-id' in response.json().keys())

	@responses.activate
	def test_post_after_authentication(self):
		responses.add(responses.POST, url + '/authenticate',
			json= resp['authentication'], status=201)
		responses.add(responses.POST, url + '/endpoints/' + deviceName + path,
			json= resp['executeRequest'], status=202)
		responses.add(responses.GET, url + '/notification/pull',
			json= resp['notifications'], status=200)
		opts = {
		 'authentication' : True,
		 'username': 'admin',
		 'password': 'not-same-as-name',
		 'interval': 123456
		}
		service.start(opts)
		response = service.post('/endpoints/' + deviceName + path)
		self.assertTrue(responses.calls[1].request.headers['Authorization'].find(resp['authentication']['access_token']) != -1)
		service.stop()

	def test_delete_post_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.post('/endpoints/' + deviceName + path)

	#------------------------delete------------------------
	@responses.activate
	def test_delete_return(self):
		responses.add(responses.DELETE, url + '/notification/callback',
			status=204)

		response = service.delete('/notification/callback')
		self.assertTrue(response.status_code == 204)

	@responses.activate
	def test_delete_after_authentication(self):
		responses.add(responses.POST, url + '/authenticate',
			json= resp['authentication'], status=201)
		responses.add(responses.DELETE, url + '/endpoints/' + deviceName + path,
			 status=202)
		responses.add(responses.GET, url + '/notification/pull',
			json= resp['notifications'], status=200)
		opts = {
		 'authentication' : True,
		 'username': 'admin',
		 'password': 'not-same-as-name',
		 'interval': 123456
		}
		service.start(opts)
		response = service.delete('/endpoints/' + deviceName + path)
		self.assertTrue(responses.calls[1].request.headers['Authorization'].find(resp['authentication']['access_token']) != -1)
		service.stop()

	def test_delete_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = service.delete('/notification/callback')


class TestDeviceMethods(unittest.TestCase):
	#--------------------------getObjects-------------------------------
	@responses.activate
	def test_get_objects_return(self):
		responses.add(responses.GET, url + '/endpoints/' + deviceName,
			json= resp['sensorObjects'], status=202)


		response = device.getObjects()
		self.assertTrue('uri' in response[0].keys())

	@responses.activate
	def test_get_objects_wrong_status(self):
		responses.add(responses.GET, url + '/endpoints/' + deviceName,
			status=404)

		response= None
		with self.assertRaisesRegexp(requests.HTTPError, '404'):
			response = device.getObjects()

	def test_get_objects_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = device.getObjects()

	#--------------------------read-------------------------------
	@responses.activate
	def test_read_return_async_id(self):
		responses.add(responses.GET, url + '/endpoints/' + deviceName + path,
			json= resp['readRequest'], status=202)

		idRegex = '^\d+#[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}$'
		response = device.read(path)
		self.assertRegexpMatches(response, idRegex)

	@responses.activate
	def test_read_callback_data(self):
		responses.add(responses.GET, url + '/endpoints/' + deviceName + path,
			json= resp['readRequest'], status=202)

		def callback(*args):
			self.assertTrue(isinstance(args[0], int))
			self.assertTrue(isinstance(args[1], str))

		response = device.read(path, callback)
		service._processEvents(resp['responsesOfAllOperations'])

	@responses.activate
	def test_read_wrong_status(self):
		responses.add(responses.GET, url + '/endpoints/' + deviceName + path,
			status=404)

		response= None
		with self.assertRaisesRegexp(requests.HTTPError, '404'):
			response = device.read(path)

	def test_read_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = device.read(path)

	#--------------------------write-------------------------------
	@responses.activate
	def test_write_return(self):
		responses.add(responses.PUT, url + '/endpoints/' + deviceName + path,
			json= resp['writeRequest'], status=202)


		idRegex = '^\d+#[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}$'
		response = device.write(path, tlvBuffer)
		self.assertRegexpMatches(response, idRegex)

	@responses.activate
	def test_write_callback_data(self):
		responses.add(responses.PUT, url + '/endpoints/' + deviceName + path,
			json= resp['writeRequest'], status=202)

		def callback(*args):
			self.assertTrue(isinstance(args[0], int))

		response = device.write(path, tlvBuffer, callback)
		service._processEvents(resp['responsesOfAllOperations'])

	@responses.activate
	def test_write_wrong_status(self):
		responses.add(responses.PUT, url + '/endpoints/' + deviceName + path,
			status=404)

		response= None
		with self.assertRaisesRegexp(requests.HTTPError, '404'):
			response = device.write(path, tlvBuffer)

	def test_write_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = device.write(path, tlvBuffer)

	#----------------------------execute--------------------------------
	@responses.activate
	def test_execute_return(self):
		responses.add(responses.POST, url + '/endpoints/' + deviceName + path,
			json= resp['executeRequest'], status=202)

		idRegex = '^\d+#[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}$'
		response = device.execute(path)
		self.assertRegexpMatches(response, idRegex)

	@responses.activate
	def test_execute_callback_data(self):
		responses.add(responses.POST, url + '/endpoints/' + deviceName + path,
			json= resp['executeRequest'], status=202)

		def callback(*args):
			self.assertTrue(isinstance(args[0], int))
			self.assertTrue(isinstance(args[1], str))

		response = device.execute(path)
		service._processEvents(resp['responsesOfAllOperations'])

	@responses.activate
	def test_execute_wrong_status(self):
		responses.add(responses.POST, url + '/endpoints/' + deviceName + path,
			status=404)

		response= None
		with self.assertRaisesRegexp(requests.HTTPError, '404'):
			response = device.execute(path)

	def test_execute_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = device.execute(path)

	#----------------------------observe--------------------------------
	@responses.activate
	def test_observe_return(self):
		responses.add(responses.PUT, url + '/subscriptions/' + deviceName + path,
			json= resp['observeRequest'], status=202)

		idRegex = '^\d+#[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}$'
		response = device.observe(path)
		self.assertRegexpMatches(response, idRegex)

	@responses.activate
	def test_observe_callback_data(self):
		responses.add(responses.PUT, url + '/subscriptions/' + deviceName + path,
			json= resp['observeRequest'], status=202)

		def callback(*args):
			self.assertTrue(isinstance(args[0], int))
			self.assertTrue(isinstance(args[1], str))

		response = device.observe(path)
		service._processEvents(resp['responsesOfAllOperations'])

	@responses.activate
	def test_observe_wrong_status(self):
		responses.add(responses.PUT, url + '/subscriptions/' + deviceName + path,
			status=404)

		response= None
		with self.assertRaisesRegexp(requests.HTTPError, '404'):
			response = device.observe(path)

	def test_observe_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = device.observe(path)

	#--------------------------cancelObserve-------------------------------
	@responses.activate
	def test_cancel_observe_return(self):
		responses.add(responses.DELETE, url + '/subscriptions/' + deviceName + path,
			status=204)


		response = device.cancelObserve(path)
		self.assertTrue(response == 204)


	def test_cancel_observe_connection_failed(self):
		response= None
		with self.assertRaises(Exception):
			response = device.cancelObserve(path)

if __name__ == '__main__':
	unittest.main()
