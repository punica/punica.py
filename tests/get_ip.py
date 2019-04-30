from netifaces import interfaces, ifaddresses, AF_INET


def get_ip_address():
    ip = 'localhost'
    for iface_name in interfaces():
        addresses = [i['addr'] for i in ifaddresses(
            iface_name).setdefault(AF_INET, [{'addr': ''}])]
        if addresses[0] and addresses[0] != '127.0.0.1':
            ip = addresses[0]
            break
    return ip
