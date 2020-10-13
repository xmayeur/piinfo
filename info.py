#!/usr/bin/env python
from __future__ import division
from __future__ import print_function

import json
import os
import socket
from subprocess import PIPE, Popen
from time import sleep

import oyaml
import paho.mqtt.client as mqtt
import psutil
import redis

FILE = r'piinfo.conf'
if os.name == 'nt':
    filename = FILE
else:
    filename = os.path.join('/etc/default', FILE)
config = oyaml.load(open(filename, 'r'), Loader=oyaml.Loader)

mqtt_host = config['mqtt']['host']
uid = config['mqtt']['uid']
connect_flag = False


def get_vault(uid):
    global config
    host = config['redis']['host']
    port = config['redis']['port']
    vaultdb = config['redis']['vaultdb']
    vault = redis.Redis(host=host, port=port, db=vaultdb)
    _s = vault.get(uid)
    _id = json.loads(_s)
    if id:
        _username = _id['username']
        _password = _id['password']
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
    global mqtt_host
    
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
        client.connect(mqtt_host, port=1883)
        while not connect_flag:
            print('+')
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
                client.connect(mqtt_host, port=1883)
                while not connect_flag:
                    print('.')  # ,  end='')
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

        # disk_total = disk.total / 2 ** 30  # GiB.
        # disk_used = disk.used / 2 ** 30
        # disk_free = disk.free / 2 ** 30
        # disk_percent_used = disk.percent
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
