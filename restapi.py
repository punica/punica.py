import requests
import json
import threading
import event_emitter
import socket

class Service(event_emitter.EventEmitter):
	def __init__(self, opts = None):
		super(Service, self).__init__()
		self.config = {
			'host' : 'http://localhost:8888',
			'ca' : '',
			'authentication' : False,
			'username' : '',
			'password' : '',
			'interval' : 1.234,
			'polling' : True,
			'port' : 5725
		}
		if not opts == None:
			self.configure(opts)
		self.authenticationToken = ''
		self.tokenValidation = 3600

	def configure(self, opts):
		for opt in opts:
			self.config[opt] = opts[opt];

	def start(self, opts = None):
		try:
			if not opts == None:
				self.configure(opts)
			if self.config['authentication']:
				self.authenticationEvent = threading.Event()
				self._startAuthenticate()
			if self.config['polling']:
				self.pullEvent = threading.Event()
				self._pullAndProcess()
			else:
				self.server = threading.Thread(target = self.createServer)
				self.server.start()
				self.registerNotificationCallback()
		except Exception, e:
			raise e;

	def stop(self):
		if self.config['authentication']:
			self.authenticationEvent.set()
		if self.config['polling']:
			self.pullEvent.set()
		else:
			self.shutDownServer()

	def getDevices(self):
		try:
			response = self.get('/endpoints')
			if (response.status_code == 200):
				return response.json()
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def getVersion(self):
		try:
			response = self.get('/version')
			if (response.status_code == 200):
				return response.text
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def pullNotification(self):
		try:
			response = self.get('/notification/pull')
			if (response.status_code == 200):
				return response.json()
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def _pullAndProcess(self):
		try:
			self._processEvents(self.pullNotification())
		except Exception, e:
			print('Failed to pull notification: ', e)
		finally:
			self.t = threading.Timer(self.config['interval'], self._pullAndProcess)
			if not self.pullEvent.is_set():
				self.t.start()

	def _startAuthenticate(self):
		try:
			data = self.authenticate()
			self.authenticationToken = data['access_token']
			self.tokenValidation = data['expires_in']
		except Exception, e:
			print('Failed to authenticate user: ', e)
		finally:
			self.authenticateTimer = threading.Timer(0.9 * self.tokenValidation, self._startAuthenticate)
			if not self.authenticationEvent.is_set():
					self.authenticateTimer.start()

	def createServer(self):
		self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.s.bind(('localhost', 5725))
		self.s.listen(10)
		self.serverRun = True

		while self.serverRun:
			conn, addr = self.s.accept()		
			data = conn.recv(1024)
			dataSplit = data.split('{"registrations"');
			dataJson = json.loads('{"registrations"' + dataSplit[1])
			
			reply = 'OK...' + data
			if not data: 
				break
			conn.sendall(reply)
			conn.close()
			self._processEvents(dataJson)
		self.s.close()

	def authenticate(self):
		try:
			data = {
			'name': self.config['username'],
			'secret': self.config['password']
			}
			dataType = 'application/json'
			response = self.post('/authenticate', data, dataType)
			if (response.status_code == 201):
				data = response.json()
				return data
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def shutDownServer(self):
		deleteNotificationCallback()
		self.serverRun = False

	def registerNotificationCallback(self):
		try:
			data = {
				'url': 'http://localhost:5725/notification',
				'headers': {}
			}
			contentType = 'application/json'
			response = self.put('/notification/callback', data, contentType)
			if (response.status_code == 204):
				data = response.text
				return data
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def deleteNotificationCallback(self):
		try:
			response = self.delete('/notification/callback')
			return response.status_code
		except Exception, e:
			raise e;

	def _processEvents(self, data):
		for i in data['registrations']:
			self.emit('register', i['name'])

		for i in data['reg-updates']:
			self.emit('update', name = i['name'])

		for i in data['de-registrations']:
			self.emit('deregister', i['name'])

		responses = sorted(data['async-responses'], key=lambda k: k['timestamp']) 
		for i in range(0, len(responses)):
			res = responses[i]
			self.emit('async-response', response = res)

	def get(self, path):
		url = self.config['host'] + path
		requestData = {
			'url': url,
			'headers': {},
		}

		if self.config['authentication']:
			requestData['headers']['Authorization'] = 'Bearer ' + self.authenticationToken

		if not self.config['ca'] == '':
			requestData['verify'] = self.config['ca']
		try:
			r = requests.get(**requestData)
			return r
		except requests.ConnectionError, e:
			raise e

	def put(self, path, argument = None, contentType = 'application/vnd.oma.lwm2m+tlv'):
		url = self.config['host'] + path
		requestData = {
			'url': url,
			'headers': {},
		}

		if argument != None:
			if contentType == 'application/json':
				requestData['json'] = argument
			else:
				requestData['data'] = argument
			requestData['headers']['content-Type']  = contentType

		if self.config['authentication']:
			requestData['headers']['Authorization'] = 'Bearer ' + self.authenticationToken

		if not self.config['ca'] == '':
			requestData['verify'] = self.config['ca']
		try:
			r = requests.put(**requestData)
			return r
		except requests.ConnectionError, e:
			raise e

	def post(self, path, argument = None, contentType = 'application/vnd.oma.lwm2m+tlv'):
		url = self.config['host'] + path
		requestData = {
			'url': url,
			'headers': {},
		}

		if argument != None:
			if contentType == 'application/json':
				requestData['json'] = argument
			else:
				requestData['data'] = argument
			requestData['headers']['content-Type']  = contentType

		if self.config['authentication']:
			requestData['headers']['Authorization'] = 'Bearer ' + self.authenticationToken

		if not self.config['ca'] == '':
			requestData['verify'] = self.config['ca']
		try:
			r = requests.post(**requestData)
			return r
		except requests.ConnectionError, e:
			raise e

	def delete(self, path):
		url = self.config['host'] + path
		requestData = {
			'url': url,
			'headers': {},
		}

		if self.config['authentication']:
			requestData['headers']['Authorization'] = 'Bearer ' + self.authenticationToken

		if not self.config['ca'] == '':
			requestData['verify'] = self.config['ca']
		try:
			r = requests.delete(**requestData)
			return r
		except requests.ConnectionError, e:
			raise e

class Device(event_emitter.EventEmitter):
	def __init__(self, service, ID):
		super(Device, self).__init__()
		
		self.service = service;
		self.ID = ID;
		self.transactions = {};
		self.observations = {};
		
		def register(name):
			if (self.ID == name):
				self.emit('register')
		self.service.on('register', register)
				
		def update(name):
			if (self.ID == name):
				self.emit('update')
		self.service.on('update', update)
		
		def deregister(name):
			if (self.ID == name):
				self.emit('deregister')
		self.service.on('deregister', deregister)
		
		def asyncResponseHandle(response):
			ID = response['id'];
			code = response['status'];
			data = response['payload'];
			if ID in self.transactions:
				self.transactions[ID](code, data)
				del self.transactions[ID]
			if ID in self.observations:
				self.observations[ID](code, data)
		self.service.on('async-response', asyncResponseHandle)
		
	def addAsyncCallback(self, ID, callback):
		self.transactions[ID] = callback
		
	def getObjects(self):
		try:
			response = self.service.get('/endpoints/'+self.ID)
			if (response.status_code == 202):
				data = response.json()
				return data
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def read(self, path, callback):
		try:
			response = self.service.get('/endpoints/'+self.ID+path)
			if (response.status_code == 202):
				data = response.json()
				ID = data['async-response-id']
				self.addAsyncCallback(ID, callback)
				return ID
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def write(self, path, callback, payload, contentType = 'application/vnd.oma.lwm2m+tlv'):
		try:
			response = self.service.put('/endpoints/' + self.ID + path, payload, contentType)
			if (response.status_code == 202):
				data = response.json()
				ID = data['async-response-id']
				self.addAsyncCallback(ID, callback)
				return ID
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def execute(self, path, callback, payload, contentType = 'text/plain'):
		try:
			response = self.service.post('/endpoints/' + self.ID + path, payload, contentType)
			if (response.status_code == 202):
				data = response.json()
				ID = data['async-response-id']
				self.addAsyncCallback(ID, callback)
				return ID
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def observe(self, path, callback):
		try:
			response = self.service.put('/subscriptions/' + self.ID + path)
			if (response.status_code == 202):
				data = response.json()
				ID = data['async-response-id']
				self.observations[ID] = callback
				return ID
			else:
				raise requests.HTTPError(response.status_code)
		except Exception, e:
			raise e;

	def cancelObserve(self, path, callback):
		try:
			response = self.service.delete('/subscriptions/' + self.ID + path)
			return response.status_code
		except Exception, e:
			raise e;


