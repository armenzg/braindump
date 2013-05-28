import re
import sys
import urllib
import subprocess
import imp

if __name__ == '__main__':
    from optparse import OptionParser
    try:
        import simplejson as json
    except:
        import json
    
    parser = OptionParser("""%%prog [options]""")
    
    parser.set_defaults(
        device="",
        )
    parser.add_option("-f", "--devices-file", dest="devices_file", help="list/url of devices.json")
    parser.add_option("-d", "--device", dest="device")

    options, actions = parser.parse_args()

    if not options.devices_file:
        parser.error("devices-file is required")
    if not options.device:
        parser.error("device is required")

    all_devices = json.load(urllib.urlopen(options.devices_file))

    found = False
    relayhost = ""
    bank  = ""
    relay = ""
    for key in all_devices:
        match = re.search(options.device, key)
        if match:
            relayhost = all_devices[key]["relayhost"]
            relayid = all_devices[key]["relayid"]
            bank, relay = relayid.split(':',2)
            found = True
    if found == False:
        print options.device, " not found in ", options.devices_file
    else:
       reboot = imp.load_source('powercyle', '/Users/kmoir/hg/relay-control/relay.py')
       bank, relay = int(bank), int(relay)
       reboot.powercycle(relayhost, bank, relay)
