

def test_404error(client):
    response = client.get("/foo/bar")
    assert response.status_code == 404
    assert response.json["code"] == 404
    assert response.json["name"] == "Not Found"
    assert response.json["description"] == "The requested URL was not found on the server. If you entered the URL manually please check your spelling and try again."