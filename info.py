#!/usr/bin/env python

from __future__ import division
from __future__ import print_function

import json
import logging as log
import socket
import sys
from platform import machine, system
from subprocess import PIPE, Popen
from time import sleep

import paho.mqtt.client as mqtt
import psutil
from getSecrets import get_secret

connect_flag = False


def get_cpu_temperature():
    try:
        if 'arm' in machine() or 'aarch64' in machine():
            process = Popen(['vcgencmd', 'measure_temp'], stdout=PIPE)
            output, _error = process.communicate()
            output = output.decode()
            return float(output[output.index('=') + 1:output.rindex("'")])
        elif 'Linux' in system() and 'x86' in machine():
            process = Popen(['sensors', '-j'], stdout=PIPE)
            output, error = process.communicate()
            data = json.loads(output)
            return float(data['coretemp-isa-0000']['Core 0']['temp2_input'])
    except:
        return None


def on_message(client, userdata, message):
    hname = socket.gethostname()
    topic = message.topic
    msg = str(message.payload.decode('utf-8'))
    print('Received message: ' + topic + '/' + msg)
    if topic == hname + '/getStatus':
        client.publish(hname + '/status', 'alive', qos=0, retain=False)


def on_connect(client, userdata, flags, rc, properties=None):
    global connect_flag
    if rc == 0:
        print("connected ok")
        connect_flag = True


def on_disconnect(client, userdata, rc):
    if rc != 0:
        log.warning("Unexpected MQTT disconnection. Will auto-reconnect")

def main():
    global connect_flag

    # Wait for the vault being ready
    while True:
        try:
            mqtt_config = get_secret('mqtt')
            break
        except Exception as e:
            log.warning('Vault not ready')
            sleep(10)

    try:
        username = mqtt_config['username']
        password = mqtt_config['password']
        host = mqtt_config['host']
        port = int(mqtt_config['port'])
        protocol = "mqtt"  # if port == 1883 else "mqtts"
        mqtt_url = f"{protocol}://{username}:{password}@{host}:{port}"
    except (OSError, KeyError) as e:
        log.error('Error on mqtt config data\n %s', e)
        sys.exit(1)

    hname = socket.gethostname()
    client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
    client.username_pw_set(username=username, password=password)

    # connect_flag=True

    client.subscribe(hname + '/getStatus')
    client.on_message = on_message

    client.on_connect = on_connect
    client.loop_start()

    try:
        client.connect(host, port=port)
        while not connect_flag:
            print('+')
            sleep(1)
    except:
        print('Cannot connect to mqtt broker - retrying')
        connect_flag = False
    
    while True:
        
        cpu_temperature = get_cpu_temperature()
        print('cpu temperature: ' + str(cpu_temperature) + 'C')
        try:
            client.publish(hname + '/temperature', str(cpu_temperature), qos=0, retain=False)
        except:
            connect_flag = False
            try:
                client.connect(host, port=port)
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
        print('cpu usage: ' + str(cpu_usage) + '%')
        client.publish(hname + '/CPU%', str(cpu_usage), qos=0, retain=False)
        
        ram = psutil.virtual_memory()
        ram_total = ram.total / 2 ** 20  # MiB.
        ram_used = ram.used / 2 ** 20
        ram_free = ram.free / 2 ** 20
        ram_percent_used = ram.percent
        print('free ram: ' + str(int(100 - ram_percent_used)) + '%')
        client.publish(hname + '/freeRAM%', str(int(100 - ram_percent_used)), qos=0, retain=False)
        
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
