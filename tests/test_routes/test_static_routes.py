def test_oauth_route(client):
    response = client.get("/")
    assert response.status_code == 200
    assert b"<html" in response.data.lower()


def test_redirect_html(client):
    response = client.get("/redirect.html")
    assert response.status_code == 200
    assert b"<html" in response.data.lower()


def test_select_page(client):
    response = client.get("/select")
    assert response.status_code == 200
    assert b"<html" in response.data.lower()


def test_custom_page(client):
    response = client.get("/custom")
    assert response.status_code == 200
    assert b"<html" in response.data.lower()


def test_standard_page(client):
    response = client.get("/standard")
    assert response.status_code == 200
    assert b"<html" in response.data.lower()


def test_success_page(client):
    response = client.get("/success")
    assert response.status_code == 200
    assert b"redirecting to the selection page" in response.data.lower()


def test_deploying_page(client):
    response = client.get("/deploying")
    assert response.status_code == 200
    assert b"<html" in response.data.lower()


def test_upload_page(client):
    response = client.get("/upload")
    assert response.status_code == 200
    assert b"<html" in response.data.lower()
