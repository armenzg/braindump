import time

from boto.ec2 import connect_to_region
from boto.ec2.networkinterface import NetworkInterfaceSpecification, \
    NetworkInterfaceCollection
from boto.ec2.blockdevicemapping import BlockDeviceMapping, BlockDeviceType


conn = connect_to_region("us-west-2")
interfaces = conn.get_all_network_interfaces(
    filters={
        "tag:Name": "*-linux*-spot-*",
        "status": "available"
    }
)
j = 0
for interface in interfaces:
    if interface.tags.get("use-public-ip"):
        continue

    if interface.status != "available":
        print "skipping %s, busy" % interface
        continue

    subnet_id = interface.subnet_id
    tags = interface.tags
    private_ip_address = interface.private_ip_address
    sg_ids = [g.id for g in interface.groups]
    print "converting %s, %s, %s, %s" % (interface, subnet_id,
                                         private_ip_address, tags)

    print "About to delete"
    time.sleep(10)
    interface.delete()
    time.sleep(10)
    print "Deleted"

    new_interface = NetworkInterfaceSpecification(
        subnet_id=subnet_id, private_ip_address=private_ip_address,
        delete_on_termination=False,
        groups=sg_ids,
        associate_public_ip_address=True
    )
    spec = NetworkInterfaceCollection(new_interface)

    bdm = BlockDeviceMapping()
    bd = BlockDeviceType()
    bd.size = 8
    bd.delete_on_termination = True
    bdm["/dev/xvda"] = bd

    reservation = conn.run_instances(
        image_id="ami-040c8634",
        key_name="aws-releng",
        instance_type="m1.medium",
        block_device_map=bdm,
        network_interfaces=spec,
    )
    print "Got res", reservation

    time.sleep(20)
    i = reservation.instances[0]
    for name, value in tags.items():
        i.interfaces[0].add_tag(name, value)
        i.interfaces[0].add_tag("use-public-ip", "1")

    print "Terminating"
    i.terminate()
    j += 1
    print "terminated, sleep 10"
    time.sleep(10)
    if j == 15:
        exit(0)
