import json

config = json.load(open("config.json"))
credentials = json.load(open("credentials.json"))

print(config)
print(credentials)