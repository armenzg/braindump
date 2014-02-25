import json
from subprocess import call

devices_file = './tools/buildfarm/mobile/devices.json'
tegra_list   = './tegra_list'

devices_fh   = open(devices_file)
devices = json.load(devices_fh)

with open(tegra_list) as f:
    hung_tegras = f.readlines()

for tegra in sorted(hung_tegras):
    tegra = tegra.rstrip()
    print tegra
    if devices[tegra]:
        foopy = devices[tegra]['foopy']
        tegra_num = tegra.split('-')[1]
        buildbot_cmd = 'kill -9 `ps auxww | grep buildbot | grep %s | awk \'{print \$2;}\'`' % tegra
        powercycle_cmd = 'cd /builds && python sut_tools/tegra_powercycle.py %s' % tegra_num
        print buildbot_cmd
        call(['ssh', 'cltbld@%s' % foopy, buildbot_cmd])
        print powercycle_cmd
        call(['ssh', 'cltbld@%s' % foopy, powercycle_cmd])


