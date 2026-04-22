def test_admin_list_loads(client):
    response = client.get("/")
    assert response.status_code == 200
    assert "Add Item" in response.text


def test_new_item_form_loads(client):
    response = client.get("/items/new")
    assert response.status_code == 200
    assert "<form" in response.text


def test_catalog_loads(client):
    response = client.get("/catalog")
    assert response.status_code == 200


def test_create_item_redirects(client):
    response = client.post(
        "/items/new",
        data={"title": "Couch", "description": "Blue", "price": "50.00", "status": "available"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_created_item_appears_in_list(client):
    client.post("/items/new", data={"title": "Chair", "description": "", "price": "10.00", "status": "available"})
    response = client.get("/")
    assert "Chair" in response.text


def test_created_item_appears_in_catalog(client):
    client.post("/items/new", data={"title": "Table", "description": "Oak", "price": "80.00", "status": "available"})
    response = client.get("/catalog")
    assert "Table" in response.text


def test_edit_item_form_loads(client):
    client.post("/items/new", data={"title": "Lamp", "description": "", "price": "5.00", "status": "available"})
    response = client.get("/items/1/edit")
    assert response.status_code == 200
    assert "Lamp" in response.text


def test_update_item(client):
    client.post("/items/new", data={"title": "Old Name", "description": "", "price": "5.00", "status": "available"})
    client.post("/items/1/edit", data={"title": "New Name", "description": "", "price": "8.00", "status": "sold"})
    response = client.get("/")
    assert "New Name" in response.text


def test_delete_item(client):
    client.post("/items/new", data={"title": "Gone", "description": "", "price": "1.00", "status": "available"})
    client.post("/items/1/delete")
    response = client.get("/")
    assert "Gone" not in response.text
