# punica
This module demonstrates Service and Device
## Service
```python
Service(self, opts=None)
```
This class represents Punica API service
Constructor initializes default configurations. Reconfigures with given options.

Parameters:
opts (object): Options object (optional)

### configure
```python
Service.configure(self, opts)
```
Configures service configuration with given options.

Parameters:
opts (object): Options object (optional)

### start
```python
Service.start(self, opts=None)
```
(Re)starts authentication,
socket listener creation and notification callback registration
or notification polling processes.

Parameters:
opts (object): Options object (optional)

### stop
```python
Service.stop(self)
```
Stops receiving and processing events
Stops this service and all it's subservices
that were started in start().
Cleans up resources

### get_devices
```python
Service.get_devices(self)
```
Sends request to get all registered endpoints, that are
currently registered to the LwM2M service.

Returns:
list: List of endpoints

### get_version
```python
Service.get_version(self)
```
Sends request to get Punica server version.

Returns:
str: Punica server's version

### pull_notification
```python
Service.pull_notification(self)
```
Sends request to get pending/queued notifications.

Returns:
object: notification data (registrations,
deregistrations, updates, async responses)

### create_server
```python
Service.create_server(self)
```
Creates socket listener.
### authenticate
```python
Service.authenticate(self)
```
Sends request to authenticate user.

Returns:
object: authentication data (token and after what time it expires)

### shut_down_server
```python
Service.shut_down_server(self)
```
Shuts down socket listener
### register_notification_callback
```python
Service.register_notification_callback(self)
```
Sends request to register notification callback.
### check_notification_callback
```python
Service.check_notification_callback(self)
```
Sends request to check whether or not notification

Returns:
object: notification callback data

### delete_notification_callback
```python
Service.delete_notification_callback(self)
```
Sends request to delete notification callback

Returns:
int: HTTP status code

### get
```python
Service.get(self, path)
```
Performs GET requests with given path.

Parameters:
path (str): Request path

Returns:
object: Object with data and response objects

### put
```python
Service.put(self, path, argument=None, content_type='application/vnd.oma.lwm2m+tlv')
```
Performs PUT requests with given path, data and data type.

Parameters:
path (str): Request path
argument (object): Data which will be sent (optional)
content_type (str): Data type (optional)

Returns:
object: Object with data and response objects

### post
```python
Service.post(self, path, argument=None, content_type='application/vnd.oma.lwm2m+tlv')
```
Performs POST requests with given path, data and data type.

Parameters:
path (str): Request path
argument (object): Data which will be sent (optional)
content_type (str): Data type (optional)

Returns:
object: Object with data and response objects

### delete
```python
Service.delete(self, path)
```
Performs DELETE requests with given path.

Parameters:
path (str): Request path

Returns:
object: Object with data and response objects

## Device
```python
Device(self, service, name)
```
This class represents device (endpoint).
### add_async_callback
```python
Device.add_async_callback(self, async_id, callback)
```
Adds a callback to transactions list. Key value is device's id.

Parameters:
path (str): Request path
callback (function): Callback which will be called when async response is received

### get_objects
```python
Device.get_objects(self)
```
Sends request to get all device's objects.

Returns:
object: Dictonary with device's objects

### read
```python
Device.read(self, path, callback=None)
```
Sends request to read device's resource data.

Parameters:
path (str): Resource path
callback (function): Callback which will be called when async response is received

Returns:
str: async response id

### write
```python
Device.write(self, path, callback=None, payload=None, content_type='application/vnd.oma.lwm2m+tlv')
```
Sends request to write a value into device's resource.

Parameters:
path (str): Resource path
callback (function): Callback which will be called when async response is received
payload (bytearray):  Data (optional)
content_type (str): Content type (optional)

Returns:
str: async response id

### execute
```python
Device.execute(self, path, callback=None, payload=None, content_type='text/plain')
```
Sends request to execute device's resource.

Parameters:
path (str): Resource path
callback (function): Callback which will be called when async response is received
payload (bytearray):  Data (optional)
content_type (str): Content type (optional)

Returns:
str: async response id

### observe
```python
Device.observe(self, path, callback=None)
```
Sends request to subscribe to resource.

Parameters:
path (str): Resource path
callback (function): Callback which will be called when async response is received

Returns:
str: async response id

### cancel_observe
```python
Device.cancel_observe(self, path)
```
Sends request to cancel subscriptions.

Parameters:
path (str): Resource path

Returns:
int: HTTP status code

# tlv

This module stores LwM2M TLV parsing methods

## binary_to_integer
```python
binary_to_integer(binary_data)
```
Converts bytes to integer.

Parameters:
binaryData (bytearray): Buffer which will be converted.

Returns:
int: Integer value.

## binary_to_bit_string
```python
binary_to_bit_string(binary_data)
```
Converts bytes to string.

Parameters:
binaryData (bytearray): Buffer which will be converted.

Returns:
str: String value.

## get_dictionary_by_value
```python
get_dictionary_by_value(dictionary_list, key_name, value)
```
Gets dictionary by given name of the key and value.

Parameters:
dictionary_list (object): Dictionary list.
key_name (object|str): Name of the key
value (object|str|int): Value

Returns:
object|str|int: dictionary

## change_buffer_size
```python
change_buffer_size(buff, start, end=None)
```
Changes buffer size.

Parameters:
buff (bytearray): Bytearray which size will be changed.
start (bytearray): Bytearray's start index.
start (bytearray): Bytearray's end index. (optional)

Returns:
bytearray: New size bytearray

## decode
```python
decode(buff)
```
Decodes any TLV bytearray.

Parameters:
buff (bytearray): encoded TLV bytearray

Returns:
object: Decoded object

## decode_resource_value
```python
decode_resource_value(buff, resource)
```
Decodes value of the resource.

Parameters:
buff (bytearray): Bytearray which will be decoded
resource (object): Object which stores resource value's type

Returns:
object|str|int|bool: Decoded value in specified type

## decode_multi_resource_instances
```python
decode_multi_resource_instances(buff, resources)
```
Decodes multiple resource TLV byte array.

Parameters:
buff (bytearray): TLV byte array
resources (object): Object which stores identifier and resource type

Returns:
object: Decoded resource.

## decode_resource
```python
decode_resource(buff, resource)
```
Decodes resource.

Parameters:
buff (bytearray): Resource TLV byte array
resources (object): Object which stores identifier and resource type

Returns:
object: Decoded resource.

## encode_resource_value
```python
encode_resource_value(resource)
```
Encodes value of the resource.

Parameters:
resource (object): Object which stores resource value and value's type

Returns:
bytearray: Byte array of encoded value

## encode
```python
encode(obj)
```
Encodes ant type of instance (Object instance, multiple resources,
resources instance, resource).

Parameters:
obj (object): Object which stores type, identifier and value

Returns:
bytearray: Encoded TLV byte array

## encode_resource_instance
```python
encode_resource_instance(resource_instance)
```
Encodes resource instance to TLV byte array.
resources instance, resource).

Parameters:
resource_instance (object): Object which stores resource identifier,
value and it's type.

Returns:
bytearray: Byte array in TLV format

## encode_multiple_resources_tlv
```python
encode_multiple_resources_tlv(resources)
```
Encodes multiple resource values to TLV byte array.

Parameters:
resources (object): Object which stores identifier, resource type,
and multiple values

Returns:
bytearray: TLV byte array

## encode_resource
```python
encode_resource(resource)
```
Encodes resource to TLV byte array.

Parameters:
resource (object): Object which stores resource identifier, type and value.

Returns:
bytearray: TLV byte array

## encode_object_instance
```python
encode_object_instance(object_instance)
```
Encodes LwM2M object instance to TLV byte array.

Parameters:
object_instance (object): LwM2M object instance

Returns:
bytearray: TLV byte array

## encode_object
```python
encode_object(obj)
```
Encodes LwM2M object to TLV byte array

Parameters:
obj (object): LwM2M object

Returns:
bytearray: TLV byte array

## decode_resource_instance
```python
decode_resource_instance(buff, resources)
```
Decodes resource instance.

Parameters:
buff (bytearray): Resource instance TLV byte array
resources (object): Object which stores resource identifier and resource type

Returns:
object: Object which stores resource identifier,
tlvSize resource type and value.

## decode_resource_instance_value
```python
decode_resource_instance_value(buff, resource_instance)
```
Decodes resource instance value

Parameters:
buff (bytearray): Resource instance TLV byte array
resource_instance (object): Object which stores resource type

Returns:
object: Decoded resource value

## decode_object_instance
```python
decode_object_instance(buff, object_instance)
```
Decodes object instance from TLV byte array.

Parameters:
buff (bytearray): TLV byte array
object_instance (object): Object which stores object instance identifier and resources

Returns:
object:  Decoded object instance

## decode_object
```python
decode_object(buff, obj)
```
Decodes LwM2M object to TLV byte array.

Parameters:
buff (bytearray): TLV byte array
obj (object): Object which stores object instances with their resources

Returns:
object:  Decoded object

