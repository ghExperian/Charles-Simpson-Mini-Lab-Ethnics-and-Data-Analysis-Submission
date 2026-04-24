from fastapi.testclient import TestClient
from main import app, create_access_token

client = TestClient(app)

def test_login_success():
    response = client.post("/token", data={"username": "admin", "password": "securepassword123"})
    assert response.status_code == 200
    assert "access_token" in response.json()

def test_get_tracts_unauthorized():
    response = client.get("/tracts/")
    assert response.status_code == 401

def test_get_tracts_authorized():
    token = create_access_token({"sub": "admin"})
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/tracts/", headers=headers)
    assert response.status_code == 200
    assert len(response.json()) > 0