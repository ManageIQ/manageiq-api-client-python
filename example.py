import os
from manageiq_client.api import ManageIQClient as MiqApi

url = os.environ.get('MIQURL') or 'http://localhost:3000/api'
auth = {}
if os.environ.has_key("MIQTOKEN"):
    auth['x-auth-token'] = os.environ.get('MIQTOKEN')
else:
    auth['user'] = os.environ.get('MIQUSERNAME') or 'admin'
    auth['password'] = os.environ.get('MIQPASSWORD') or 'smartvm'


client = MiqApi(url, auth)

print("\nManageIQ version: {0}".format(client.version))
print("\nVirtual Machines Collection\n")

for vm in client.collections.vms.all:
    print(vm.name)
