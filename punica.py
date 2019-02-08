'''
This module demonstrates Service and Device
'''
import json
import threading
import socket
import httplib
import event_emitter
import requests

class Service(event_emitter.EventEmitter):
    def __init__(self, opts=None):
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
        self.authentication_token = ''
        self.token_validation = 3600

    def configure(self, opts):
        for opt in opts:
            self.config[opt] = opts[opt]

    def start(self, opts=None):
        try:
            if opts is not None:
                self.configure(opts)
            self.stop()
            if self.config['authentication']:
                self.authentication_event = threading.Event()
                self._start_authenticate()
            if self.config['polling']:
                self.pull_event = threading.Event()
                self._pull_and_process()
            else:
                self.server = threading.Thread(target=self.create_server)
                self.server.start()
                self.register_notification_callback()
        except Exception as ex:
            raise ex

    def stop(self):
        if hasattr(self, 'authentication_event'):
            self.authentication_event.set()
            self.authenticate_timer.cancel()
            #del self.authentication_event

        if hasattr(self, 'pull_event'):
            self.pull_event.set()
            self.pull_timer.cancel()
            #del self.pull_event

        if hasattr(self, 'server_run') and self.server_run:
            self.shut_down_server()
            #del self.server_run

    def get_devices(self):
        try:
            response = self.get('/endpoints')
            if response.status_code == 200:
                return response.json()
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def get_version(self):
        try:
            response = self.get('/version')
            if response.status_code == 200:
                return response.json()
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def pull_notification(self):
        try:
            response = self.get('/notification/pull')
            if response.status_code == 200:
                return response.json()
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def _pull_and_process(self):
        try:
            self._process_events(self.pull_notification())
        except Exception as ex:
            print('Failed to pull notification: ', ex)
        finally:
            self.pull_timer = threading.Timer(
                self.config['interval'], self._pull_and_process)
            if not self.pull_event.is_set():
                self.pull_timer.start()

    def _start_authenticate(self):
        try:
            data = self.authenticate()
            self.authentication_token = data['access_token']
            self.token_validation = data['expires_in']
        except Exception as ex:
            print('Failed to authenticate user: ', ex)
        finally:
            self.authenticate_timer = threading.Timer(
                0.9 * self.token_validation, self._start_authenticate)
            if not self.authentication_event.is_set():
                self.authenticate_timer.start()

    def create_server(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind(('', 5725))
        self.sock.listen(10)
        self.sock.settimeout(10)
        self.server_run = True
        while self.server_run:
            conn, addr = self.sock.accept()
            data = conn.recv(1024)
            if not data:
                break
            (headers, json_data) = data.split("\r\n\r\n")
            if json_data:
                parsed_json = json.loads(json_data)
            reply = 'OK...' + data

            conn.sendall(reply)
            conn.close()
            if parsed_json:
                processEventsThread = threading.Thread(
                    target=self._process_events, args=(parsed_json,))
                processEventsThread.start()
        self.sock.close()

    def authenticate(self):
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
        self.server_run = False
        conn = httplib.HTTPConnection("localhost", self.config['port'])
        conn.request("PUT", "/notification", '')
        self.delete_notification_callback()

    def register_notification_callback(self):
        try:
            data = {
                'url': 'http://localhost:5725/notification',
                'headers': {}
            }
            content_type = 'application/json'
            response = self.put('/notification/callback', data, content_type)
            if response.status_code == 204:
                return response.status_code
            else:
                raise requests.HTTPError(response.status_code)
        except Exception as ex:
            raise ex

    def delete_notification_callback(self):
        try:
            response = self.delete('/notification/callback')
            return response.status_code
        except Exception as ex:
            raise ex

    def _process_events(self, data):
        for i in data['registrations']:
            self.emit('register', i['name'])

        for i in data['reg-updates']:
            self.emit('update', name=i['name'])

        for i in data['de-registrations']:
            self.emit('deregister', i['name'])

        responses = sorted(data['async-responses'],
                           key=lambda k: k['timestamp'])
        for i in range(0, len(responses)):
            res = responses[i]
            self.emit('async-response', response=res)

    def get(self, path):
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
    def __init__(self, service, name):
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
        self.transactions[async_id] = callback

    def get_objects(self):
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
        try:
            response = self.service.delete('/subscriptions/' + self.name + path)
            return response.status_code
        except Exception as ex:
            raise ex
