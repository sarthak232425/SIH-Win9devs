import requests

token_endpoint = 'https://icdaccessmanagement.who.int/connect/token'
client_id = '92da78bf-fc34-4dc0-9784-1a80ef29bee2_e75ac5d4-9e99-4fba-a686-3d160d4a4c0b'
client_secret = '3caWeOo3eJbx/8zW6Agxb2ecbKvECV7Y6o1MQJj/9CI='
scope = 'icdapi_access'
grant_type = 'client_credentials'


# get the OAUTH2 token

# set data to post
payload = {'client_id': client_id, 
	   	   'client_secret': client_secret, 
           'scope': scope, 
           'grant_type': grant_type}
           
# make request
r = requests.post(token_endpoint, data=payload, verify=False).json()
token = r['access_token']



# # access ICD API

# uri = 'https://id.who.int/icd/entity'
uri = 'http://id.who.int/icd/entity/2072376338'

# HTTP header fields to set
headers = {'Authorization':  'Bearer '+token, 
           'Accept': 'application/json', 
           'Accept-Language': 'en',
	   'API-Version': 'v2'}
           
# make request           
r = requests.get(uri, headers=headers, verify=False)

# print the result
print (r.text)			