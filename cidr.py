from geoip2fast import GeoIP2Fast
import dns.resolver
import ipaddress
import traceback
import json
import sys
import dns

def check_ip_is_lan(ip_address_str):
    try:
        ip_obj = ipaddress.ip_address(ip_address_str)
        return ip_obj.is_private
    except:
        return False

def cidr_to_ip_list(cidr_notation):
    try:
        network = ipaddress.ip_network(cidr_notation)
        ip_addresses = [str(ip) for ip in network]
        return ip_addresses
    except:
        # print(traceback.format_exc())
        return []

def limit_cidr(ip, result):
    arr = result.asn_cidr.split('/')
    if int(arr[1]) < 21:
        ip_arr = ip.split('.')
        with open('cidr.log', 'a') as f:
            f.write(result.asn_cidr + ': ' + result.asn_name + '\n')
        return "{}.{}.{}.0/24".format(ip_arr[0], ip_arr[1], ip_arr[2])
    else:
        return result.asn_cidr

asn_cloud_keyword_list = [
    # A
    'akamai',
    'alibaba',
    'aliyun',
    'amazon',
    'apple',
    'aws',
    'azure',
    # B
    'baidu',
    'baiducloud',
    # C
    'cdn77',
    'cdnetworks',
    'chinaunicom',
    'chinamobile',
    'chinanet',
    'cloudflare',
    'cloudfront',
    'cloud',
    'colocrossing',
    'contabo',
    'coreweave',
    # D
    'digitalocean',
    'dreamhost',
    # E
    'equinix',
    'edgecast',
    # F
    'fastly',
    'facebook',
    # G
    'gcore',
    'google',
    'gcp',
    'godaddy',
    # H
    'hetzner',
    'hostinger',
    'huawei',
    'huaweicloud',
    # I
    'incapsula',
    'ibm',
    'ibmcloud',
    'ionos',
    # J
    'japanic',
    # K
    'keycdn',
    'kt',
    'kddi',
    # L
    'linode',
    'liquidweb',
    # M
    'megaport',
    'microsoft',
    'megafon',
    'maxcdn',
    # N
    'netlify',
    'ntt',
    'nhn',
    # O
    'oracle',
    'ovh',
    'ovhcloud',
    'orange',
    # P
    'packet',
    'pinterest',
    'protonmail',
    # Q
    'qcloud',
    'qingcloud',
    # R
    'rackspace',
    'redhat',
    'robinhood',
    # S
    'salesforce',
    'sakura',
    'scaleway',
    'stackpath',
    'softlayer',
    'sina',
    'singtel',
    'spacex',
    'starlink',
    # T
    'tencent',
    'telekom',
    'telefonica',
    'telia',
    'tata',
    'twitch',
    'twitter',
    'tiktok',
    # U
    'upcloud',
    'unity',
    'uber',
    # V
    'verizon',
    'vultr',
    'vmware',
    # W
    'wangsu',
    'wix',
    'whatsapp',
    # X
    'xiaomi',
    # Y
    'yandex',
    'yahoo',
    # Z
    'zenlayer',
    'zoho',
]

no_cloud = False
cloud_info = {}
if len(sys.argv) > 1 and sys.argv[1] == '--no-cloud':
    with open('cloud_providers.json', 'r') as f:
        cloud_info = json.loads(f.read())
    no_cloud = True

geoip = GeoIP2Fast(geoip2fast_data_file="geoip2fast-asn.dat.gz")

ip_list = []

for line in sys.stdin:
    try:
        result = dns.resolver.resolve(line[:-1], 'A')
        for ip in result:
            ip_list.append(ip.to_text().strip())
    except:
        pass

ip_list = list(set(ip_list))
sorted_ips = sorted([ipaddress.ip_address(ip) for ip in ip_list])
sorted_ips_str = [str(ip) for ip in sorted_ips]
# print(sorted_ips_str)

full_ip_list = []

for ip in sorted_ips_str:
    if check_ip_is_lan(ip):
        continue
    if ip in full_ip_list:
        continue

    is_cloud = False
    for info in cloud_info.values():
        cidrs = info['cidrs']
        for c in cidrs:
            try:
                i = ipaddress.ip_address(ip)
                n = ipaddress.ip_network(c)
                if i in n:
                    is_cloud = True
                    break
            except:
                # print(traceback.format_exc())
                pass
        if is_cloud:
            break
    if is_cloud:
        continue

    try:
        result = geoip.lookup(ip)
        if result:
            if no_cloud:
                is_cloud = False
                for keyword in asn_cloud_keyword_list:
                    if keyword in result.asn_name.lower():
                        is_cloud = True
                        break
                if is_cloud:
                    continue
            # print(result.asn_cidr + ': ' + result.asn_name)
            cidr_ip_list = cidr_to_ip_list(limit_cidr(ip, result))
            for cidr_ip in cidr_ip_list:
                if cidr_ip not in full_ip_list:
                    full_ip_list.append(cidr_ip)
        else:
            if ip not in full_ip_list:
                full_ip_list.append(ip)
    except:
        # print(traceback.format_exc())
        pass

# print(full_ip_list)
for ip in full_ip_list:
    print(ip)
    