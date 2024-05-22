import requests

from connectivity.gateio.Utils import genSignRest

host = "https://api.gateio.ws"
prefix = "/api/v4"
headers = {'Accept': 'application/json', 'Content-Type': 'application/json'}

url = '/account/detail'
#url = '/account/stp_groups'
query_param = ''

sign_headers = genSignRest('GET', prefix + url, query_param)
headers.update(sign_headers)
r = requests.request('GET', host + prefix + url, headers=headers)
print(r.json())




