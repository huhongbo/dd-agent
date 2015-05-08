#!/usr/bin/env python
import re
import subprocess as sp
import sys


def _is_number(a_string):
    try:
        float(a_string)
    except ValueError:
        return False
    return True


def _flatten_devices(devices):
    # Some volumes are stored on their own line. Rejoin them here.
    previous = None
    for parts in devices:
        if len(parts) == 1:
            previous = parts[0]
        elif previous and _is_number(parts[0]):
            # collate with previous line
            parts.insert(0, previous)
            previous = None
        else:
            previous = None
    return devices

try:
    prtconf = sp.Popen(['prtconf'], stdout=sp.PIPE, close_fds=True).communicate()[0]
    dfk_out = sp.Popen(['df', '-k'], stdout=sp.PIPE, close_fds=True).communicate()[0]
    nets_out = sp.Popen(['netstat', '-in'], stdout=sp.PIPE, close_fds=True).communicate()[0]
    cpu_out = sp.Popen(['pmcycles', '-m'], stdout=sp.PIPE, close_fds=True).communicate()[0]
    kernel = sp.Popen(['oslevel', '-s'], stdout=sp.PIPE, close_fds=True).communicate()[0]
    all_cpu = [l for l in cpu_out.split("\n") if len(l) > 0]
except StandardError:
    print "command execute error"

core = len(all_cpu)
lines = prtconf.split('\n')
regexp = re.compile(r'([A-Z].*):\s?(.*)')
conf = {}
for line in lines:
    try:
        match = re.search(regexp, line)
        if match is not None:
            conf[match.group(1)] = match.group(2)
    except Exception:
        print "prtconf parse error"

all_devices = [l.strip().split() for l in dfk_out.split("\n")]
raw_devices = [l for l in all_devices[1:] if l]
devices = _flatten_devices(raw_devices)
usage_data = []
filesystem = {}
for parts in devices:
    if parts[-1] != "/proc":
        try:
            filesystem['kb_size'] = parts[1]
            filesystem['mounted_on'] = parts[-1]
            filesystem['name'] = parts[0]
        except IndexError:
            print "error"
        usage_data.append(dict(filesystem))
conf['IP Address'] = "10.70.41.126"
regex = r"([a-z]+\d).*" + re.escape(conf['IP Address'])
lines = nets_out.split('\n')
for line in lines:
    try:
        match = re.search(regex, line)
        if match is not None:
            netif = match.group(1)
    except Exception:
        print "netstat parse error"
regex = r"" + re.escape(netif) + r".*(\w+(?:\.\w+){5})"
for line in lines:
    try:
        match = re.search(regex, line)
        if match is not None:
            mac = match.group(1)
    except Exception:
        print "netstat parse error"
ints = mac.split('.')
for i in range(len(ints)):
    if len(ints[i]) == 1:
        ints[i] = '0' + ints[i]
mac = ":".join(ints)
cpu = {}
platform = {}
mem = {}
network = {}
ohai = {}
cpu['cpu_cores'] = int(core) / int(conf['Number Of Processors'])
cpu['family'] = conf['Processor Version']
clock = conf['Processor Clock Speed'].split(' ')
cpu['mhz'] = clock[0]
cpu['model'] = conf['Processor Implementation Mode']
cpu['model_name'] = conf['Processor Type']
cpu['stepping'] = ''
cpu['vendor_id'] = 'IBM'
platform['GOOARCH'] = ''
platform['GOOS'] = ''
platform['goV'] = ''
platform['hostname'] = conf['Host Name']
platform['kernel_name'] = 'AIX'
platform['kernel_release'] = kernel[0] + "." + kernel[1]
platform['kernel_version'] = kernel[0:-1]
platform['machine'] = conf['System Model']
platform['os'] = 'AIX'
platform['processor'] = conf['Processor Type']
platform['pythonV'] = sys.version[0:5]
platform['sn'] = conf['Machine Serial Number']
mem['swap_total'] = str(int(conf['Total Paging Space'][0:-2]) * 1024) + "kB"
mem['total'] = str(int(conf['Memory Size'][0:-3]) * 1024) + "kB"
network['ipaddress'] = conf['IP Address']
network['ipaddressv6'] = ''
network['macaddress'] = mac
ohai['cpu'] = cpu
ohai['filesystem'] = usage_data
ohai['memory'] = mem
ohai['network'] = network
ohai['platform'] = platform
sys.stdout.write(str(ohai))
