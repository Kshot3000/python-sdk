from octaspace import OctaSpaceClient

with OctaSpaceClient(api_key="your-api-key") as client:
    print(client.network.info().data)
    print(client.accounts.profile().data)
