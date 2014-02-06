import random
from boto.ec2 import connect_to_region
from boto.vpc import VPCConnection
from boto.ec2.networkinterface import NetworkInterfaceSpecification, \
    NetworkInterfaceCollection
from boto.ec2.blockdevicemapping import BlockDeviceMapping, BlockDeviceType
import time

config = {
    "us-east-1": {
        "range": range(100, 200),
        "domain": "build.releng.use1.mozilla.com",
        "subnet_ids": ["subnet-2ba98340", "subnet-2da98346", "subnet-22a98349",
                       "subnet-0822004e", "subnet-2da98346", "subnet-a93b31cb",
                       "subnet-5bc7c62f"],
        "ami": "ami-ea8e1e83",
    },
    "us-west-2": {
        "range": range(400, 500),
        "domain": "build.releng.usw2.mozilla.com",
        "subnet_ids": ["subnet-d748dabe", "subnet-a848dac1",
                       "subnet-ad48dac4", "subnet-c74f48b3"],
        "ami": "ami-040c8634",
    }
}

slave_types = {
    "bld-linux64": "bld-linux64-spot-%03i",
}


def avail_subnet(conn, subnet_ids):
    vpc = VPCConnection(region=conn.region)
    for subnet_id in subnet_ids:
        subnet = vpc.get_all_subnets(subnet_ids=[subnet_id])[0]
        if int(subnet.available_ip_address_count) > 0:
            return subnet_id
    raise ValueError


for region, region_config in config.iteritems():
    print "# working in", region
    conn = connect_to_region(region)
    subnet_ids = region_config["subnet_ids"]
    domain = region_config["domain"]
    slave_range = region_config["range"]
    ami = region_config["ami"]

    for slave_type, pattern in slave_types.iteritems():
        for i in slave_range:
            name = pattern % i
            fqdn = "%s.%s" % (name, domain)
            cname = "%s.build.mozilla.org" % name
            random.shuffle(subnet_ids)
            subnet_id = avail_subnet(conn, subnet_ids)
            new_interface = NetworkInterfaceSpecification(
                subnet_id=subnet_id, private_ip_address=None,
                delete_on_termination=False,
                groups=[],
                associate_public_ip_address=True
            )
            spec = NetworkInterfaceCollection(new_interface)

            bdm = BlockDeviceMapping()
            bd = BlockDeviceType()
            bd.size = 8
            bd.delete_on_termination = True
            bdm["/dev/xvda"] = bd

            reservation = conn.run_instances(
                image_id=ami,
                key_name="aws-releng",
                instance_type="m1.medium",
                block_device_map=bdm,
                network_interfaces=spec,
            )
            print "# Got res", reservation

            time.sleep(20)
            i = reservation.instances[0]
            i.interfaces[0].add_tag("Name", name)
            i.interfaces[0].add_tag("FQDN", fqdn)
            i.interfaces[0].add_tag("moz-type", slave_type)
            i.interfaces[0].add_tag("use-public-ip", "1")
            ip = i.interfaces[0].private_ip_address

            print "# Terminating"
            i.terminate()
            print "# Adding", fqdn, cname, subnet_id, ip
            print 'invtool A create --ip %s --fqdn %s --private  --description "spot instance"' % (ip, fqdn)
            print 'invtool PTR create --ip %s --target %s --private --description "spot instance"' % (ip, fqdn)
            print 'invtool CNAME create --fqdn %s --target %s --private --description "spot instance"' % (cname, fqdn)
            time.sleep(1)
