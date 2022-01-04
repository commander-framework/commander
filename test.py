import requests

certPath = "./volumes/capy/certs/proxy/proxy.crt"
keyPath = "./volumes/capy/certs/proxy/proxy.pem"
caPath = "./volumes/capy/ca.crt"
url = "https://localhost/agent/jobs"
cert = (certPath, keyPath)

response = requests.get(url, verify=caPath, cert=cert)

print(response.status_code, response.json())
