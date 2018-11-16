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
		self.authenticationToken = ''
		self.tokenValidation = 3600

	def start(self):
		if self.config['polling']:
			self.pullEvent = threading.Event()
			self._pullAndProcess()
		else:
			self.server = threading.Thread(target = self.createServer)
			self.server.start()
			self.registerNotificationCallback()

	def stop(self):
		if self.config['polling']:
			self.pullEvent.set()
		else:
			self.shutDownServer()
		
	def pullNotification(self):
		response = self.get('/notification/pull')
		return response.json()
		
	def _pullAndProcess(self):
		self._processEvents(self.pullNotification())
		self.t = threading.Timer(self.config['interval'], self._pullAndProcess)
		if not self.pullEvent.is_set():
				self.t.start()
				
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
			
	def shutDownServer(self):
		#deleteCallback()
		self.serverRun = False
				
	def registerNotificationCallback(self):
		data = {
			'url': 'http://localhost:5725/notification',
			'headers': {}
		}
		contentType = 'application/json';
		response = self.put('/notification/callback', data, contentType)
		if (response.status_code == 204):
			data = response.text
			return data
		else:
			return response.status_code
		
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
		headers = {}
			
		if self.config['authentication']:
			headers['Authorization'] = 'Bearer ' + self.authenticationToken

		url = self.config['host'] + path
		r = requests.get(url, headers = headers)
		return r

	def put(self, path, argument = None, contentType = 'application/vnd.oma.lwm2m+tlv'):
		data = {}
		headers = {}

		if argument != None:
			headers['content-Type']  = contentType
			data = argument
			
		if self.config['authentication']:
			headers['Authorization'] = 'Bearer ' + self.authenticationToken
      
		url = self.config['host'] + path
		if contentType == 'application/json':
			r = requests.put(url, headers = headers, json = data)
		else:
			r = requests.put(url, headers = headers, data = data)
		return r
		

	def post(self, path, argument = None, contentType = 'application/vnd.oma.lwm2m+tlv'):
		data = {}
		headers = {}

		if argument != None:
			headers['content-Type']  = contentType
			data = argument
			
		if self.config['authentication']:
			headers['Authorization'] = 'Bearer ' + self.authenticationToken
      
		url = self.config['host'] + path
		if contentType == 'application/json':
			r = requests.post(url, headers = headers, json = data)
		else:
			r = requests.post(url, headers = headers, data = data)
		return r

	def delete(self, path):
		headers = {}

		if self.config['authentication']:
			headers['Authorization'] = 'Bearer ' + self.authenticationToken
      
		url = self.config['host'] + path
		r = requests.delete(url, headers = headers)
		return r
		
		
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
		response = self.service.get('/endpoints/'+self.ID)
		if (response.status_code == 202):
			data = response.json()
			return data
		else:
			return response.status_code
		
	def read(self, path, callback):
		response = self.service.get('/endpoints/'+self.ID+path)
		if (response.status_code == 202):
			data = response.json()
			ID = data['async-response-id']
			self.addAsyncCallback(ID, callback)
			return ID
		else:
			return response.status_code
			
	def write(self, path, callback, payload, contentType = 'application/vnd.oma.lwm2m+tlv'):
		response = self.service.put('/endpoints/' + self.ID + path, payload, contentType)
		if (response.status_code == 202):
			data = response.json()
			ID = data['async-response-id']
			self.addAsyncCallback(ID, callback)
			return ID
		else:
			return response.status_code
			
	def execute(self, path, callback, payload, contentType = 'text/plain'):
		response = self.service.post('/endpoints/' + self.ID + path, payload, contentType)
		if (response.status_code == 202):
			data = response.json()
			ID = data['async-response-id']
			self.addAsyncCallback(ID, callback)
			return ID
		else:
			return response.status_code
			
	def observe(self, path, callback):
		response = self.service.put('/subscriptions/' + self.ID + path)
		if (response.status_code == 202):
			data = response.json()
			ID = data['async-response-id']
			self.observations[ID] = callback
			return ID
		else:
			return response.status_code
			
	def cancelObserve(self, path, callback):
		response = self.service.delete('/subscriptions/' + self.ID + path)
		return response.status_code
		

