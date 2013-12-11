import random
from boto.ec2 import connect_to_region
from boto.vpc import VPCConnection
import time

config = {
    "us-east-1": {
        "range": range(1, 200),
        "domain": "try.releng.use1.mozilla.com",
        "subnet_ids": ["subnet-27a9834c", "subnet-39a98352", "subnet-3ea98355",
                       "subnet-93b285e7", "subnet-e5bacacd", "subnet-ef373f8d",
                       "subnet-cd83d28b"]
    },
    "us-west-2": {
        "range": range(300, 499),
        "domain": "try.releng.usw2.mozilla.com",
        "subnet_ids": ["subnet-ae48dac7", "subnet-a348daca", "subnet-a448dacd",
                       "subnet-72b68206"]
    }
}

slave_types = {
    "try-linux64": "try-linux64-spot-%03i",
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
