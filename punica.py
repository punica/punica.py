"""This module demonstrates Service and Device"""
import json
import threading
import socket
import httplib
import event_emitter
import requests
import netifaces


class Service(event_emitter.EventEmitter):
    """This class represents Punica API service
    Constructor initializes default configurations. Reconfigures with given options.

    Parameters:
    opts (object): Options object (optional)
    """

    def __init__(self, opts=None):
        # pylint: disable=too-many-instance-attributes
        super(Service, self).__init__()
        self.config = {
            'host': 'http://localhost:8888',
            'ca': '',
            'authentication': False,
            'username': '',
            'password': '',
            'interval': 1.234,
            'polling': True,
            'port': 5725
        }
        if opts is not None:
            self.configure(opts)
        self.get_ip_address()
        self.authentication_token = ''
        self.token_validation = 3600
        self.pull_event = threading.Event()
        self.server_run = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.authentication_event = threading.Event()
        self.server = threading.Thread(target=self.create_server)
        self.pull_timer = threading.Timer(
            self.config['interval'], self._pull_and_process)
        self.authenticate_timer = threading.Timer(
            0.9 * self.token_validation, self._start_authenticate)

    def configure(self, opts):
        """Configures service configuration with given options.

        Parameters:
        opts (object): Options object (optional)
        """
        for opt in opts:
            self.config[opt] = opts[opt]

    def get_ip_address(self):
        """Finds interface and sets IP address. Ignores loopback address."""
        self.ip_address = 'localhost'
        for iface_name in netifaces.interfaces():
            addresses = [i['addr'] for i in netifaces.ifaddresses(
                iface_name).setdefault(netifaces.AF_INET, [{'addr': ''}])]
            if addresses[0] and addresses[0] != '127.0.0.1':
                self.ip_address = addresses[0]
                break

    def start(self, opts=None):
        """(Re)starts authentication,
        socket listener creation and notification callback registration
        or notification polling processes.

        Parameters:
        opts (object): Options object (optional)
        """
        try:
            if opts is not None:
                self.configure(opts)
            self.stop()
            if self.config['authentication']:
                self.authentication_event.set()
                self._start_authenticate()
            if self.config['polling']:
                self.pull_event.set()
                self._pull_and_process()
            else:
                self.server.start()
                self.register_notification_callback()
        except Exception as ex:
            raise ex

    def stop(self):
        """Stops receiving and processing events
        Stops this service and all it's subservices
        that were started in start().
        Cleans up resources
        """
        if self.authentication_event.is_set():
            self.authentication_event.clear()
            self.authenticate_timer.cancel()

        if self.pull_event.is_set():
            self.pull_event.clear()
            self.pull_timer.cancel()

        if hasattr(self, 'server_run') and self.server_run:
            self.shut_down_server()

    def get_devices(self):
        """Sends request to get all registered endpoints, that are
        currently registered to the LwM2M service.

        Returns:
        list: List of endpoints
        """
        try:
            response = self.get('/endpoints')
            if response.status_code == 200:
                return response.json()
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def get_version(self):
        """Sends request to get Punica server version.

        Returns:
        str: Punica server's version
        """
        try:
            response = self.get('/version')
            if response.status_code == 200:
                return response.json()
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def pull_notification(self):
        """Sends request to get pending/queued notifications.

        Returns:
        object: notification data (registrations,
        deregistrations, updates, async responses)
        """
        try:
            response = self.get('/notification/pull')
            if response.status_code == 200:
                return response.json()
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def _pull_and_process(self):
        """Starts pulling and processing notifications"""
        try:
            self._process_events(self.pull_notification())
        except Exception as ex:
            print('Failed to pull notification: ', ex)
        finally:
            self.pull_timer = threading.Timer(
                self.config['interval'], self._pull_and_process)
            if self.pull_event.is_set():
                self.pull_timer.start()

    def _start_authenticate(self):
        """Starts authenticating"""
        try:
            data = self.authenticate()
            self.authentication_token = data['access_token']
            self.token_validation = data['expires_in']
        except Exception as ex:
            print('Failed to authenticate user: ', ex)
        finally:
            self.authenticate_timer = threading.Timer(
                0.9 * self.token_validation, self._start_authenticate)
            if self.authentication_event.is_set():
                self.authenticate_timer.start()

    def create_server(self):
        """Creates socket listener."""
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', 5725))
        self.sock.listen(10)
        self.sock.settimeout(10)
        self.server_run = True
        while self.server_run:
            (conn, _) = self.sock.accept()
            data = conn.recv(1024)
            if not data:
                break
            (_, json_data) = data.split("\r\n\r\n")
            if json_data:
                parsed_json = json.loads(json_data)
            reply = 'OK...' + data

            conn.sendall(reply)
            conn.close()
            if parsed_json:
                process_events_thread = threading.Thread(
                    target=self._process_events, args=(parsed_json,))
                process_events_thread.start()
        self.sock.close()

    def authenticate(self):
        """Sends request to authenticate user.

        Returns:
        object: authentication data (token and after what time it expires)
        """
        try:
            data = {
                'name': self.config['username'],
                'secret': self.config['password']
            }
            content_type = 'application/json'
            response = self.post('/authenticate', data, content_type)
            if response.status_code == 201:
                data = response.json()
                return data
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def shut_down_server(self):
        """Shuts down socket listener"""
        self.server_run = False
        conn = httplib.HTTPConnection("localhost", self.config['port'])
        conn.request("PUT", "/notification", '')
        self.delete_notification_callback()

    def register_notification_callback(self):
        """Sends request to register notification callback."""
        try:
            data = {'url': 'http://' + self.ip_address + ':' +
                           str(self.config['port']) + '/notification', 'headers': {}}
            content_type = 'application/json'
            response = self.put('/notification/callback', data, content_type)
            if response.status_code == 204:
                return response.status_code
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def check_notification_callback(self):
        """Sends request to check whether or not notification

        Returns:
        object: notification callback data
        """
        try:
            response = self.get('/notification/callback')
            if response.status_code == 200:
                data = response.json()
                protocol = 'http://'
                if self.config['ca']:
                    protocol = 'https://'
                if data['url'] == protocol + self.ip_address + ':' + \
                        str(self.config['port']) + '/notification':
                    return data
                else:
                    raise Exception(
                        {
                            'message': 'Invalid notification callback is registered',
                            'status': 'EINVALIDCALLBACK'
                        }
                    )
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def delete_notification_callback(self):
        """Sends request to delete notification callback

        Returns:
        int: HTTP status code
        """
        try:
            response = self.delete('/notification/callback')
            return response.status_code
        except Exception as ex:
            raise ex

    def _process_events(self, data):
        """Handles notification data and emits events.

        Parameters:
        data (object): Events - Notifications (registrations,
        reg-updates, de-registrations, async-responses)
        """
        for i in data['registrations']:
            self.emit('register', i['name'])

        for i in data['reg-updates']:
            self.emit('update', name=i['name'])

        for i in data['de-registrations']:
            self.emit('deregister', i['name'])

        responses = sorted(data['async-responses'],
                           key=lambda k: k['timestamp'])
        for resp in responses:
            self.emit('async-response', response=resp)

    def get(self, path):
        """Performs GET requests with given path.

        Parameters:
        path (str): Request path

        Returns:
        object: Object with data and response objects
        """
        url = self.config['host'] + path
        request_data = {
            'url': url,
            'headers': {},
        }

        if self.config['authentication']:
            request_data['headers']['Authorization'] = 'Bearer ' + \
                self.authentication_token

        if self.config['ca'] != '':
            request_data['verify'] = self.config['ca']
        try:
            req = requests.get(**request_data)
            return req
        except requests.ConnectionError as ex:
            raise ex

    def put(
            self,
            path,
            argument=None,
            content_type='application/vnd.oma.lwm2m+tlv'):
        """Performs PUT requests with given path, data and data type.

        Parameters:
        path (str): Request path
        argument (object): Data which will be sent (optional)
        content_type (str): Data type (optional)

        Returns:
        object: Object with data and response objects
        """
        url = self.config['host'] + path
        request_data = {
            'url': url,
            'headers': {},
        }

        if argument is not None:
            if content_type == 'application/json':
                request_data['json'] = argument
            else:
                request_data['data'] = argument
            request_data['headers']['content-Type'] = content_type

        if self.config['authentication']:
            request_data['headers']['Authorization'] = 'Bearer ' + \
                self.authentication_token

        if self.config['ca'] != '':
            request_data['verify'] = self.config['ca']
        try:
            req = requests.put(**request_data)
            return req
        except requests.ConnectionError as ex:
            raise ex

    def post(
            self,
            path,
            argument=None,
            content_type='application/vnd.oma.lwm2m+tlv'):
        """Performs POST requests with given path, data and data type.

        Parameters:
        path (str): Request path
        argument (object): Data which will be sent (optional)
        content_type (str): Data type (optional)

        Returns:
        object: Object with data and response objects
        """
        url = self.config['host'] + path
        request_data = {
            'url': url,
            'headers': {},
        }

        if argument is not None:
            if content_type == 'application/json':
                request_data['json'] = argument
            else:
                request_data['data'] = argument
            request_data['headers']['content-Type'] = content_type

        if self.config['authentication']:
            request_data['headers']['Authorization'] = 'Bearer ' + \
                self.authentication_token

        if self.config['ca'] != '':
            request_data['verify'] = self.config['ca']
        try:
            req = requests.post(**request_data)
            return req
        except requests.ConnectionError as ex:
            raise ex

    def delete(self, path):
        """Performs DELETE requests with given path.

        Parameters:
        path (str): Request path

        Returns:
        object: Object with data and response objects
        """
        url = self.config['host'] + path
        request_data = {
            'url': url,
            'headers': {},
        }

        if self.config['authentication']:
            request_data['headers']['Authorization'] = 'Bearer ' + \
                self.authentication_token

        if self.config['ca'] != '':
            request_data['verify'] = self.config['ca']
        try:
            req = requests.delete(**request_data)
            return req
        except requests.ConnectionError as ex:
            raise ex


class Device(event_emitter.EventEmitter):
    """This class represents device (endpoint)."""

    def __init__(self, service, name):
        """Constructor initiliazes given service object, device's id
        and starts listening for events emited by service (when device
        registers, updates, deregisters, sends data), handles "async
        responses" and emits "register", "update", "deregister" events.

        Parameters:
        service (object): Service object
        id (str): Endpoint id
        """
        super(Device, self).__init__()

        self.service = service
        self.name = name
        self.transactions = {}
        self.observations = {}

        def register(name):
            if self.name == name:
                self.emit('register')
        self.service.on('register', register)

        def update(name):
            if self.name == name:
                self.emit('update')
        self.service.on('update', update)

        def deregister(name):
            if self.name == name:
                self.emit('deregister')
        self.service.on('deregister', deregister)

        def async_response_handle(response):
            async_response_id = response.get('id')
            code = response.get('status')
            data = response.get('payload')
            if not self.transactions.get(async_response_id) is None:
                self.transactions[async_response_id](code, data)
                del self.transactions[async_response_id]
            if not self.observations.get(async_response_id) is None:
                self.observations[async_response_id](code, data)
        self.service.on('async-response', async_response_handle)

    def add_async_callback(self, async_id, callback):
        """Adds a callback to transactions list. Key value is device's id.

        Parameters:
        path (str): Request path
        callback (function): Callback which will be called when async response is received
        """
        self.transactions[async_id] = callback

    def get_objects(self):
        """Sends request to get all device's objects.

        Returns:
        object: Dictonary with device's objects
        """
        try:
            response = self.service.get('/endpoints/' + self.name)
            if response.status_code == 202:
                data = response.json()
                return data
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def read(self, path, callback=None):
        """Sends request to read device's resource data.

        Parameters:
        path (str): Resource path
        callback (function): Callback which will be called when async response is received

        Returns:
        str: async response id
        """
        try:
            response = self.service.get('/endpoints/' + self.name + path)
            if response.status_code == 202:
                data = response.json()
                async_id = data['async-response-id']
                self.add_async_callback(async_id, callback)
                return async_id
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def write(self, path, callback=None, payload=None,
              content_type='application/vnd.oma.lwm2m+tlv'):
        """Sends request to write a value into device's resource.

        Parameters:
        path (str): Resource path
        callback (function): Callback which will be called when async response is received
        payload (bytearray):  Data (optional)
        content_type (str): Content type (optional)

        Returns:
        str: async response id
        """
        try:
            response = self.service.put(
                '/endpoints/' + self.name + path, payload, content_type)
            if response.status_code == 202:
                data = response.json()
                async_id = data['async-response-id']
                self.add_async_callback(async_id, callback)
                return async_id
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def execute(
            self,
            path,
            callback=None,
            payload=None,
            content_type='text/plain'):
        """Sends request to execute device's resource.

        Parameters:
        path (str): Resource path
        callback (function): Callback which will be called when async response is received
        payload (bytearray):  Data (optional)
        content_type (str): Content type (optional)

        Returns:
        str: async response id
        """
        try:
            response = self.service.post(
                '/endpoints/' + self.name + path, payload, content_type)
            if response.status_code == 202:
                data = response.json()
                async_id = data['async-response-id']
                self.add_async_callback(async_id, callback)
                return async_id
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def observe(self, path, callback=None):
        """Sends request to subscribe to resource.

        Parameters:
        path (str): Resource path
        callback (function): Callback which will be called when async response is received

        Returns:
        str: async response id
        """
        try:
            response = self.service.put('/subscriptions/' + self.name + path)
            if response.status_code == 202:
                data = response.json()
                async_id = data['async-response-id']
                self.observations[async_id] = callback
                return async_id
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def cancel_observe(self, path):
        """Sends request to cancel subscriptions.

        Parameters:
        path (str): Resource path

        Returns:
        int: HTTP status code
        """
        try:
            response = self.service.delete(
                '/subscriptions/' + self.name + path)
            return response.status_code
        except Exception as ex:
            raise ex
