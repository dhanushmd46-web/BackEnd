def get_auth_token(client,username="student_tester",password="pass123"):
    client.post("/auth/register",json={"username":username,"password":password})
    response=client.post("/auth/login",json={"username":username,"password":password})
    return response.json()["access_token"]


def auth_header(token):
    return {"Authorization":f"Bearer {token}"}

def test_get_students_without_token(client):
    response=client.get("/students/")
    assert response.status_code in [401,403]


def test_get_students_with_token(client):
    token=get_auth_token(client,username="getter_user")
    response=client.get("/students/",headers=auth_header(token))
    assert response.status_code==200
    assert isinstance(response.json(),list)


def test_create_students(client):
    token=get_auth_token(client,username="creator_user")
    response=client.post(
        "/students/",
        json={"name":"Ravi kumar","age":20,"email":"ravi@test.com","city":"kuppam"},
        headers=auth_header(token)
    )

    assert response.status_code==201
    data=response.json()
    assert data["name"]=="Ravi kumar"
    assert data["email"]=="ravi@test.com"
    assert "id" in data


def test_create_student_duplicate_email(client):
    token= get_auth_token(client,username="dup_email_user")
    student_data={"name":"Test","age":21,"email":"unique@test","city":"chennai"}
    client.post("/students/",json=student_data,headers=auth_header(token))
    response=client.post("/student/",json=student_data,headers=auth_header(token))
    assert response.status_code==404