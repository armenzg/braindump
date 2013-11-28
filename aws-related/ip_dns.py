import random
from boto.ec2 import connect_to_region
from boto.vpc import VPCConnection
import time

config = {
    "us-east-1": {
        "range": range(1, 200),
        "domain": "test.releng.use1.mozilla.com",
        "subnet_ids": ["subnet-8f32cbe5", "subnet-3835cc52", "subnet-ed35cc87",
                       "subnet-ae35ccc4", "subnet-fb97bc8f", "subnet-ff3542d7",
                       "subnet-e40e0786", "subnet-7ca5f03a"],
    },
    "us-west-2": {
        "range": range(300, 499),
        "domain": "test.releng.usw2.mozilla.com",
        "subnet_ids": ["subnet-d6cba8bf", "subnet-aecba8c7", "subnet-a4cba8cd",
                       "subnet-be89a2ca"],
    }
}

slave_types = {
    "tst-linux32": "tst-linux32-spot-%03i",
    "tst-linux64": "tst-linux64-spot-%03i",
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
    for slave_type, pattern in slave_types.iteritems():
        for i in slave_range:
            name = pattern % i
            fqdn = "%s.%s" % (name, domain)
            cname = "%s.build.mozilla.org" % name
            random.shuffle(subnet_ids)
            subnet_id = avail_subnet(conn, subnet_ids)
            netif = conn.create_network_interface(subnet_id=subnet_id)
            time.sleep(1)
            netif.add_tag("Name", name)
            netif.add_tag("FQDN", fqdn)
            netif.add_tag("moz-type", slave_type)
            ip = netif.private_ip_address
            print "# Adding", fqdn, cname, subnet_id, ip
            print 'invtool A create --ip %s --fqdn %s --private  --description "spot instance"' % (ip, fqdn)
            print 'invtool PTR create --ip %s --target %s --private --description "spot instance"' % (ip, fqdn)
            print 'invtool CNAME create --fqdn %s --target %s --private --description "spot instance"' % (cname, fqdn)
