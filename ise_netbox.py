import os
from ciscoisesdk import IdentityServicesEngineAPI
from ciscoisesdk.exceptions import ApiError
from nornir import InitNornir
from nornir.core.filter import F
from nornir_utils.plugins.tasks.data import load_yaml
from pprint import pprint
api = IdentityServicesEngineAPI(
    username = os.environ["ISE_SRV_USERNAME"],
    password = os.environ["ISE_SRV_PASSWORD"],
    base_url="https://172.31.2.16:443",
    verify=False,
)
nornir_config_file="config.yaml"
ip_list = ["10.161.13.16"]

nr_init = InitNornir(config_file = nornir_config_file)
nr_run = nr_init.filter(F(hostname__any = ip_list))
hosts_list = [host for host in nr_run.inventory.hosts]

def load_host_vars(task):
    data = task.run(
        task = load_yaml,
        severity_level=logging.DEBUG, 
        file = f"inventory/host_vars/{task.host}.yaml"
    )
    task.host["vars"] = data.result

def get_all_net_dev_ise():
    try:
        response = api.network_device.get_network_device(size=100)
        device_name_list = [name['name'] for name in response.response['SearchResult']['resources']]
    except ApiError as error:
        print(error)
    return device_name_list

for host in hosts_list:
    location = nr_run.inventory.hosts[host]['location']
    ise_hostname = nr_run.inventory.hosts[host].hostname
    ise_tacacs_key = os.environ[f"ISE_TACACS_{location}_KEY"]
    if nr_run.inventory.hosts[host].get("host_description"):
        ise_description = nr_run.inventory.hosts[host]["host_description"]
    else:
        ise_description = nr_run.inventory.hosts[host]["group_description"]
    if host in get_all_net_dev_ise():
        try:
            response = api.network_device.update_network_device_by_name(name=f"{host}", 
                                                                network_device_group_list=[f"Location#All Locations#{location}",
                                                                                            "IPSEC#Is IPSEC Device#No",
                                                                                            "Device Type#All Device Types"], 
                                                                network_device_iplist=[{"ipaddress": ise_hostname, "mask":32}],
                                                                description = ise_description,
                                                                tacacs_settings={"connectModeOptions": "OFF",
                                                                                "previousSharedSecret": "",
                                                                                "previousSharedSecretExpiry": 0,
                                                                                "sharedSecret": ise_tacacs_key},)
            print(response.response)
        except ApiError as error:
            print(error.message)
    else:
        try:
            response = api.network_device.create_network_device(name=f"{host}", 
                                                                network_device_group_list=[f"Location#All Locations#{location}",
                                                                                            "IPSEC#Is IPSEC Device#No",
                                                                                            "Device Type#All Device Types"], 
                                                                network_device_iplist=[{"ipaddress": ise_hostname, "mask":32}],
                                                                description = ise_description,
                                                                tacacs_settings={"connectModeOptions": "OFF",
                                                                                "previousSharedSecret": "",
                                                                                "previousSharedSecretExpiry": 0,
                                                                                "sharedSecret": ise_tacacs_key},)
            print(response.response)
        except ApiError as error:
            print(error.message)
