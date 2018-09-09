#!/usr/bin/env python
from __future__ import division

import socket
from subprocess import PIPE, Popen
from time import sleep

import paho.mqtt.client as mqtt
import psutil
import requests

# from sys import exit

HOST = '192.168.0.4'
vault_url = 'http://192.168.0.4:5000/api/ID'
uid = 'iot'
connect_flag = False


def get_vault(uid):
    # url = config.get('vault', 'vault_url')
    
    r = requests.get(url=vault_url + '?uid=%s' % uid)
    id = r.json()
    r.close()
    if id['status'] == 200:
        _username = id['username']
        _password = id['password']
    else:
        _username = ''
        _password = ''
    return _username, _password


def get_cpu_temperature():
    try:
        process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
        output, _error = process.communicate()
        return float(output[output.index('=') + 1:output.rindex("'")])
    except:
        return None


def on_message(client, userdata, message):
    hname = socket.gethostname()
    topic = message.topic
    msg = str(message.payload.decode('utf-8'))
    print('Received message: ' + topic + '/' + msg)
    if topic == hname + '/getStatus':
        client.publish(hname + '/status', 'alive', qos=0, retain=False)


def on_connect(client, userdata, flags, rc):
    global connect_flag
    if rc == 0:
        print("connected ok")
        connect_flag = True


def main():
    global connect_flag
    uname, pwd = get_vault(uid)
    hname = socket.gethostname()
    client = mqtt.Client('info_' + hname)
    client.username_pw_set(username=uname, password=pwd)

    # connect_flag=True

    client.subscribe(hname + '/getStatus')
    client.on_message = on_message

    client.on_connect = on_connect
    client.loop_start()


    try:
        client.connect(HOST, port=1883)
        while not connect_flag:
            print '+',  # end='')
            sleep(1)
    except:
        print('Cannot connect to mqtt broker - retrying')
        connect_flag = False

    
    while True:
        
        cpu_temperature = get_cpu_temperature()
        # print('cpu temperature: ' + str(cpu_temperature) + 'C')
        try:
            client.publish(hname + '/temperature', str(cpu_temperature), qos=0, retain=False)
        except:
            connect_flag = False
            try:
                client.connect(HOST, port=1883)
                while not connect_flag:
                    print '.',  # end='')
                    sleep(1)
                continue
            except:
                print('Cannot connect to mqtt broker')
                connect_flag = False
                sleep(15)
                continue
        
        cpu_usage = psutil.cpu_percent()
        # print('cpu usage: ' + str(cpu_usage) + '%')
        client.publish(hname + '/CPU%', str(cpu_usage), qos=0, retain=False)
        
        ram = psutil.virtual_memory()
        ram_total = ram.total / 2 ** 20  # MiB.
        ram_used = ram.used / 2 ** 20
        ram_free = ram.free / 2 ** 20
        ram_percent_used = ram.percent
        # print('free ram: ' + str(100-ram_percent_used) + '%')
        client.publish(hname + '/freeRAM%', str(100 - ram_percent_used), qos=0, retain=False)
        
        disk = psutil.disk_usage('/')
        disk_total = disk.total / 2 ** 30  # GiB.
        disk_used = disk.used / 2 ** 30
        disk_free = disk.free / 2 ** 30
        disk_percent_used = disk.percent
        #
        # Print top five processes in terms of virtual memory usage.
        #
        # processes = sorted(
        #     ((p.get_memory_info().vms, p) for p in psutil.process_iter()),
        #    reverse=True
        # )
        # for virtual_memory, process in processes[:5]:
        #    print virtual_memory // 2**20, process.pid, process.name
        sleep(15)


if __name__ == '__main__':
    main()
