import os
from manageiq_client.api import ManageIQClient as MiqApi

url = os.environ.get('MIQURL') or 'http://localhost:3000/api'
username = os.environ.get('MIQUSERNAME') or 'admin'
password = os.environ.get('MIQPASSWORD') or 'smartvm'

client = MiqApi(url, (username, password))

print("\nManageIQ version: {0}".format(client.version))
print("\nVirtual Machines Collection\n")

for vm in client.collections.vms.all:
    print(vm.name)
