class ApiClient:
    def __init__(self, transport):
        self.transport = transport

    def get_json(self, url):
        response = self.transport.get(url)
        return response.json()

    def post_json(self, url, payload):
        response = self.transport.post(url, json=payload)
        return response.json()
