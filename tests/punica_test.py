"""Tests for `punica.py`."""

import unittest
import json
import time
import httplib
import sys
import responses
import requests
from rest_response import resp
sys.path.append('../')
from punica import Service
from punica import Device

SERVICE = Service()
URL = 'http://localhost:8888'
DEVICE_NAME = 'threeSeven'
PATH = '/3312/0/5850'
TLV_BUFFER = bytearray([0xe4, 0x16, 0x44, 0x00, 0x00, 0x00, 0x01])
DEVICE = Device(SERVICE, DEVICE_NAME)


class TestServiceMethods(unittest.TestCase):
    """Tests for Service class"""
    @responses.activate
    def test_start_polling_false(self):
        """
        Should register notification callback and
        create socket listener which recieves notification
        """
        responses.add(responses.PUT, URL + '/notification/callback',
                      json=resp['registerCallback'], status=204)
        responses.add(responses.GET, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['readRequest'], status=202)
        responses.add(responses.DELETE, URL + '/notification/callback',
                      status=204)
        responses.add_passthru('http://localhost:5725/notification')
        responses.add(responses.DELETE, URL + '/notification/callback',
                      status=204)
        SERVICE.start({'polling': False, 'authentication': False})

        def callback(status, data):
            """Callback function"""
            self.assertTrue(isinstance(status, int))
            self.assertTrue(isinstance(data, unicode))
            SERVICE.stop()

        DEVICE.read(PATH, callback)
        body = json.dumps(resp['readResponse'])
        conn = httplib.HTTPConnection("localhost", 5725)
        conn.request("PUT", "/notification", body)
        SERVICE.server.join()  # test hold

    @responses.activate
    def test_start_polling_true(self):
        """
        Should send GET requests to pull out notifications
        every interval of time in ms which is set by the parameter
        when initializing service object
        """
        responses.add(responses.GET, URL + '/notification/pull',
                      json=resp['oneAsyncResponse'], status=200)
        responses.add(responses.GET, URL + '/notification/pull',
                      json=resp['oneAsyncResponse'], status=200)
        time_error = 0.02
        pull_time = []
        chosen_time = 0.2

        def async_response_callback(response):
            """Callback function which is called then notification is pulled"""
            # pylint: disable=unused-argument
            pull_time.append(time.time())
            if len(pull_time) == 2:
                SERVICE.stop()
                time_difference = abs(
                    chosen_time - pull_time[1] - pull_time[0])
                if time_difference >= time_error:
                    pulled_on_time = True
                self.assertTrue(pulled_on_time)
        SERVICE.on('async-response', async_response_callback)
        SERVICE.start({'polling': True, 'interval': chosen_time})
        SERVICE.pull_timer.join()  # test hold

    # -----------------------pull_notification----------------------------
    @responses.activate
    def test_pull_notification_return(self):
        """
        should return an object with 4 properties
        (registrations, reg-updates, de-registrations, async-responses)
        """
        responses.add(responses.GET, URL + '/notification/pull',
                      json=resp['oneAsyncResponse'], status=200)

        response = SERVICE.pull_notification()
        self.assertTrue('registrations' in response.keys())
        self.assertTrue('reg-updates' in response.keys())
        self.assertTrue('de-registrations' in response.keys())
        self.assertTrue('async-responses' in response.keys())

    @responses.activate
    def test_pull_notification_status(self):
        """
        shoud raise HTTPError if status code is not 200
        """
        responses.add(responses.GET, URL + '/notification/pull',
                      status=404)

        with self.assertRaisesRegexp(requests.HTTPError, '404'):
            SERVICE.pull_notification()

    @responses.activate
    def test_pull_notification_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.pull_notification()

    # --------------------------get_devices------------------------------
    @responses.activate
    def test_get_devices_return(self):
        """
        should return an array of all endponts with their data
        """
        responses.add(responses.GET, URL + '/endpoints',
                      json=resp['endpoints'], status=200)

        response = SERVICE.get_devices()
        self.assertTrue('name' in response[0].keys())
        self.assertTrue('type' in response[0].keys())
        self.assertTrue('status' in response[0].keys())
        self.assertTrue('q' in response[0].keys())

    @responses.activate
    def test_get_devices_wrong_status(self):
        """
        shoud raise HTTPError if status code is not 200
        """
        responses.add(responses.GET, URL + '/endpoints',
                      status=404)

        with self.assertRaisesRegexp(requests.HTTPError, '404'):
            SERVICE.get_devices()

    def test_get_devices_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.get_devices()

    # -------------------------get_version--------------------------------
    @responses.activate
    def test_get_version_return(self):
        """
        should return bytes which define the version of punica server
        """
        responses.add(responses.GET, URL + '/version',
                      json=resp['version'], status=200)

        response = SERVICE.get_version()
        self.assertEqual(response, '1.0.0')

    def test_get_version_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.get_version()

    # --------------------------authenticate----------------------------
    @responses.activate
    def test_authenticate_return(self):
        """
        should return access token and its expiry time
        """
        responses.add(responses.POST, URL + '/authenticate',
                      json=resp['authentication'], status=201)

        response = SERVICE.authenticate()
        self.assertTrue('access_token' in response.keys())
        self.assertTrue('expires_in' in response.keys())

    @responses.activate
    def test_authenticate_wrong_status(self):
        """
        shoud raise HTTPError if status code is not 201
        """
        responses.add(responses.POST, URL + '/authenticate',
                      status=400)

        with self.assertRaisesRegexp(requests.HTTPError, '400'):
            SERVICE.authenticate()

    def test_authenticate_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.authenticate()

    # ------------------register_notification_callback---------------------
    @responses.activate
    def test_reg_notification_cb_return(self):
        """
        should send PUT request to register notification callback
        """
        responses.add(responses.PUT, URL + '/notification/callback',
                      json=resp['registerCallback'], status=204)

        response = SERVICE.register_notification_callback()
        self.assertTrue(response)

    @responses.activate
    def test_reg_notification_cb_status(self):
        """
        shoud raise HTTPError if status code is not 204
        """
        responses.add(responses.PUT, URL + '/notification/callback',
                      status=404)

        with self.assertRaisesRegexp(requests.HTTPError, '404'):
            SERVICE.register_notification_callback()

    def test_reg_notification_cb_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.register_notification_callback()

    # ----------------check_notification_callback------------------------
    @responses.activate
    def test_get_notification_cb_return(self):
        """
	should return an object with valid notification callback data
	"""
	responses.add(responses.GET, URL + '/notification/callback',
                        json=resp['notificationCallback'], status=200)
	response = SERVICE.check_notification_callback()
	self.assertTrue(response == resp['notificationCallback'])

    @responses.activate
    def test_get_notification_cb_invalid(self):
	"""
	should raise exception if notification callback doesnt match service parameters
	"""
	responses.add(responses.GET, URL + '/notification/callback',
			json=resp['badNotificationCallback'], status=200)
	    with self.assertRaises(Exception):
	        SERVICE.check_notification_callback()

    def test_get_notification_cb_conn_fail(self):
        """
        should raise exception if connection is not succesfull
        """
	with self.assertRaises(Exception):
            SERVICE.check_notification_callback()

    # ----------------------delete_notification_callback-------------------
    @responses.activate
    def test_del_notification_cb_status(self):
        """
        should return status code if connection is successful
        """
        responses.add(responses.DELETE, URL + '/notification/callback',
                      status=204)

        response = SERVICE.delete_notification_callback()
        self.assertTrue(response == 204)

    def test_del_notification_cb_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.delete_notification_callback()

    # ------------------------get---------------------------
    @responses.activate
    def test_get_return(self):
        """
        should perform GET request
        """
        responses.add(responses.GET, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['readRequest'], status=202)

        response = SERVICE.get('/endpoints/' + DEVICE_NAME + PATH)
        self.assertTrue('async-response-id' in response.json().keys())

    @responses.activate
    def test_get_after_authentication(self):
        """
        should add a header with authentication token if authentication
        is enabled in configuration
        """
        responses.add(responses.POST, URL + '/authenticate',
                      json=resp['authentication'], status=201)
        responses.add(responses.GET, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['readRequest'], status=202)
        responses.add(responses.GET, URL + '/notification/pull',
                      json=resp['notifications'], status=200)
        opts = {
            'authentication': True,
            'username': 'admin',
            'password': 'not-same-as-name',
            'interval': 123456
        }
        SERVICE.start(opts)
        SERVICE.get('/endpoints/' + DEVICE_NAME + PATH)
        self.assertTrue(
            responses.calls[1].request.headers['Authorization'].find(
                resp['authentication']['access_token']) != -1)
        SERVICE.stop()

    def test_get_connection_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.get('/endpoints/' + DEVICE_NAME + PATH)

    # ------------------------put---------------------------
    @responses.activate
    def test_put_return(self):
        """
        should perform PUT request
        """
        responses.add(responses.PUT, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['writeRequest'], status=202)

        response = SERVICE.put('/endpoints/' + DEVICE_NAME + PATH, TLV_BUFFER)
        self.assertTrue('async-response-id' in response.json().keys())

    @responses.activate
    def test_put_after_authentication(self):
        """
        should add a header with authentication token if authentication
        is enabled in configuration
        """
        responses.add(responses.POST, URL + '/authenticate',
                      json=resp['authentication'], status=201)
        responses.add(responses.PUT, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['writeRequest'], status=202)
        responses.add(responses.GET, URL + '/notification/pull',
                      json=resp['notifications'], status=200)
        opts = {
            'authentication': True,
            'username': 'admin',
            'password': 'not-same-as-name',
            'interval': 123456
        }
        SERVICE.start(opts)
        SERVICE.put('/endpoints/' + DEVICE_NAME + PATH, TLV_BUFFER)
        self.assertTrue(
            responses.calls[1].request.headers['Authorization'].find(
                resp['authentication']['access_token']) != -1)
        SERVICE.stop()

    def test_put_connection_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.put(
                '/endpoints/' + DEVICE_NAME + '/' + PATH, TLV_BUFFER)

    # ------------------------post--------------------------
    @responses.activate
    def test_post_return(self):
        """
        should perform POST request
        """
        responses.add(responses.POST, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['executeRequest'], status=202)

        response = SERVICE.post('/endpoints/' + DEVICE_NAME + PATH)
        self.assertTrue('async-response-id' in response.json().keys())

    @responses.activate
    def test_post_after_authentication(self):
        """
        should add a header with authentication token if authentication
        is enabled in configuration
        """
        responses.add(responses.POST, URL + '/authenticate',
                      json=resp['authentication'], status=201)
        responses.add(responses.POST, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['executeRequest'], status=202)
        responses.add(responses.GET, URL + '/notification/pull',
                      json=resp['notifications'], status=200)
        opts = {
            'authentication': True,
            'username': 'admin',
            'password': 'not-same-as-name',
            'interval': 123456
        }
        SERVICE.start(opts)
        SERVICE.post('/endpoints/' + DEVICE_NAME + PATH)
        self.assertTrue(
            responses.calls[1].request.headers['Authorization'].find(
                resp['authentication']['access_token']) != -1)
        SERVICE.stop()

    def test_delete_post_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.post('/endpoints/' + DEVICE_NAME + PATH)

    # ------------------------delete------------------------
    @responses.activate
    def test_delete_return(self):
        """
        should perform DELETE request
        """
        responses.add(responses.DELETE, URL + '/notification/callback',
                      status=204)

        response = SERVICE.delete('/notification/callback')
        self.assertTrue(response.status_code == 204)

    @responses.activate
    def test_del_after_auth(self):
        """
        should add a header with authentication token if authentication
        is enabled in configuration
        """
        responses.add(responses.POST, URL + '/authenticate',
                      json=resp['authentication'], status=201)
        responses.add(
            responses.DELETE,
            URL +
            '/endpoints/' +
            DEVICE_NAME +
            PATH,
            status=202)
        responses.add(responses.GET, URL + '/notification/pull',
                      json=resp['notifications'], status=200)
        opts = {
            'authentication': True,
            'username': 'admin',
            'password': 'not-same-as-name',
            'interval': 123456
        }
        SERVICE.start(opts)
        SERVICE.delete('/endpoints/' + DEVICE_NAME + PATH)
        self.assertTrue(
            responses.calls[1].request.headers['Authorization'].find(
                resp['authentication']['access_token']) != -1)
        SERVICE.stop()

    def test_delete_connection_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            SERVICE.delete('/notification/callback')


class TestDeviceMethods(unittest.TestCase):
    """
    Tests for Device class
    """

    # --------------------------get_objects-------------------------------
    @responses.activate
    def test_get_objects_return(self):
        """
        should return an array of all endpont\'s resource paths
        """
        responses.add(responses.GET, URL + '/endpoints/' + DEVICE_NAME,
                      json=resp['sensorObjects'], status=202)

        response = DEVICE.get_objects()
        self.assertTrue('uri' in response[0].keys())

    @responses.activate
    def test_get_objects_wrong_status(self):
        """
        shoud raise HTTPError if status code is not 202
        """
        responses.add(responses.GET, URL + '/endpoints/' + DEVICE_NAME,
                      status=404)

        with self.assertRaisesRegexp(requests.HTTPError, '404'):
            DEVICE.get_objects()

    def test_get_objects_conn_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            DEVICE.get_objects()

    # --------------------------read-------------------------------
    @responses.activate
    def test_read_return_async_id(self):
        """
        should return async-response-id
        """
        responses.add(responses.GET, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['readRequest'], status=202)

        id_regex = '^\\d+#[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}$'
        response = DEVICE.read(PATH)
        self.assertRegexpMatches(response, id_regex)

    @responses.activate
    def test_read_callback_data(self):
        """
        should return status code in a callback function which is given as a parameter
        """
        responses.add(responses.GET, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['readRequest'], status=202)

        def callback(*args):
            """
            callback function
            """
            self.assertTrue(isinstance(args[0], int))
            self.assertTrue(isinstance(args[1], str))

        DEVICE.read(PATH, callback)
        SERVICE._process_events(resp['responsesOfAllOperations'])

    @responses.activate
    def test_read_wrong_status(self):
        """
        shoud raise HTTPError if status code is not 202
        """
        responses.add(responses.GET, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      status=404)

        with self.assertRaisesRegexp(requests.HTTPError, '404'):
            DEVICE.read(PATH)

    def test_read_connection_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            DEVICE.read(PATH)

    # --------------------------write-------------------------------
    @responses.activate
    def test_write_return(self):
        """
        should return async-response-id
        """
        responses.add(responses.PUT, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['writeRequest'], status=202)

        id_regex = '^\\d+#[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}$'
        response = DEVICE.write(PATH, TLV_BUFFER)
        self.assertRegexpMatches(response, id_regex)

    @responses.activate
    def test_write_callback_data(self):
        """
        should return status code in a callback function which is given as a parameter
        """
        responses.add(responses.PUT, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['writeRequest'], status=202)

        def callback(*args):
            """
            callback function
            """
            self.assertTrue(isinstance(args[0], int))

        DEVICE.write(PATH, callback, TLV_BUFFER)
        SERVICE._process_events(resp['responsesOfAllOperations'])

    @responses.activate
    def test_write_wrong_status(self):
        """
        shoud raise HTTPError if status code is not 202
        """
        responses.add(responses.PUT, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      status=404)

        with self.assertRaisesRegexp(requests.HTTPError, '404'):
            DEVICE.write(PATH, TLV_BUFFER)

    def test_write_connection_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            DEVICE.write(PATH, TLV_BUFFER)

    # ----------------------------execute--------------------------------
    @responses.activate
    def test_execute_return(self):
        """
        should return async-response-id
        """
        responses.add(responses.POST, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['executeRequest'], status=202)

        id_regex = '^\\d+#[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}$'
        response = DEVICE.execute(PATH)
        self.assertRegexpMatches(response, id_regex)

    @responses.activate
    def test_execute_callback_data(self):
        """
        should return status code in a callback function which is given as a parameter
        """
        responses.add(responses.POST, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      json=resp['executeRequest'], status=202)

        def callback(*args):
            """
            callback function
            """
            self.assertTrue(isinstance(args[0], int))

        DEVICE.execute(PATH, None, callback)
        SERVICE._process_events(resp['responsesOfAllOperations'])

    @responses.activate
    def test_execute_wrong_status(self):
        """
        shoud raise HTTPError if status code is not 202
        """
        responses.add(responses.POST, URL + '/endpoints/' + DEVICE_NAME + PATH,
                      status=404)

        with self.assertRaisesRegexp(requests.HTTPError, '404'):
            DEVICE.execute(PATH)

    def test_execute_connection_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            DEVICE.execute(PATH)

    # ----------------------------observe--------------------------------
    @responses.activate
    def test_observe_return(self):
        """
        should send PUT request to start observation,
        returns status code
        """
        responses.add(
            responses.PUT,
            URL +
            '/subscriptions/' +
            DEVICE_NAME +
            PATH,
            json=resp['observeRequest'],
            status=202)

        id_regex = '^\\d+#[0-9a-z]{8}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}-[0-9a-z]{4}$'
        response = DEVICE.observe(PATH)
        self.assertRegexpMatches(response, id_regex)

    @responses.activate
    def test_observe_callback_data(self):
        """
        should send PUT request to start observation,
        callback function is called when data and status code are received
        """
        responses.add(
            responses.PUT,
            URL +
            '/subscriptions/' +
            DEVICE_NAME +
            PATH,
            json=resp['observeRequest'],
            status=202)

        def callback(*args):
            """
            callback function
            """
            self.assertTrue(isinstance(args[0], int))
            self.assertTrue(isinstance(args[1], str))

        DEVICE.observe(PATH, callback)
        SERVICE._process_events(resp['responsesOfAllOperations'])

    @responses.activate
    def test_observe_wrong_status(self):
        """
        shoud raise HTTPError if status code is not 202
        """
        responses.add(
            responses.PUT,
            URL +
            '/subscriptions/' +
            DEVICE_NAME +
            PATH,
            status=404)

        with self.assertRaisesRegexp(requests.HTTPError, '404'):
            DEVICE.observe(PATH)

    def test_observe_connection_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            DEVICE.observe(PATH)

    # --------------------------cancel_observe-------------------------------
    @responses.activate
    def test_cancel_observe_return(self):
        """
        should send DELETE request to stop observation, returns status code
        """
        responses.add(
            responses.DELETE,
            URL +
            '/subscriptions/' +
            DEVICE_NAME +
            PATH,
            status=204)

        response = DEVICE.cancel_observe(PATH)
        self.assertTrue(response == 204)

    def test_cancel_observe_conn_failed(self):
        """
        shoud raise exception if connection is not succesfull
        """
        with self.assertRaises(Exception):
            DEVICE.cancel_observe(PATH)


if __name__ == '__main__':
    unittest.main()
