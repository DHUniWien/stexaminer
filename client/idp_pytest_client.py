import requests
import pytest

class idpTestClient:
    def __init__(self, base_url):
        self.base_url = base_url
        self.session = requests.Session()

    def make_fixture_request(self, fixid):
        r = self.session.post(f"{self.base_url}/request/{fixid}")
        r.raise_for_status()
        return r.json()

    def query_job(self, jobid):
        r = self.session.get(f"{self.base_url}/query/{jobid}")
        r.raise_for_status()
        return r.json()

    def make_delete_request(self, jobid):
        r = self.session.post(f"{self.base_url}/delete_request/{jobid}")
        r.raise_for_status()

    def close(self):
        self.session.close()


@pytest.fixture(scope="session")
def app():
    """
    Session-wide idp test client.
    """
    client = idpTestClient(
        base_url="http://localhost:8001"
    )

    yield client

    client.close()        
