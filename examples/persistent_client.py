from octaspace import OctaSpaceClient

with OctaSpaceClient(api_key="your-api-key", keep_alive=True, pool_size=10) as client:
    print(client.transport_stats())
    print(client.sessions.list().data)
