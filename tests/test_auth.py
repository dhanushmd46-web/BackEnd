def test_register_success(client):
    response=client.post(
        "/auth/register",
        json={"username":"testuser","password":"testpass123"}

    )
    assert response.status_code==201
    assert response.json()["message"]=="Account created for testuser"


def test_register_duplicate_username(client):
    client.post("/auth/register",json={"username":"dupuser","password":"pass123"})
    response=client.post(
        "/auth/register",
        json={"username":"dupuser","password":"differentpass"}
    )
    assert response.status_code==400
    assert "Username already taken" in response.json()["detail"]

def test_login_success(client):
    client.post("/auth/register",json={"username":"loginuser","password":"mypassword"})
    response=client.post(
        "/auth/login",
        json={"username":"loginuser","password":"mypassword"}
    )

    assert response.status_code==200
    data=response.json()
    assert "access_token" in data
    assert data["token_type"]=="bearer"


def test_login_wrong_password(client):
    client.post("/auth/register",json={"username":"user_wrong","password":"correctpass"})
    response=client.post(
        "/auth/login",
        json={"username":"user_wrong","password":"wrongpassword"}
    )
    assert response.status_code==400
    assert "Invalid credentials" in response.json()["detail"]


def test_login_nonexistent_user(client):
    response=client.post(
        "/auth/login",
        json={"username":"nobody","password":"anyting"}
    )
    assert response.status_code==400