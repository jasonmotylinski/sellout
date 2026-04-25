import database


def test_catalog_loads(client):
    response = client.get("/")
    assert response.status_code == 200


def test_admin_list_loads(client):
    response = client.get("/admin")
    assert response.status_code == 200
    assert "Add item" in response.text


def test_new_item_form_loads(client):
    response = client.get("/admin/items/new")
    assert response.status_code == 200
    assert "<form" in response.text


def test_create_item_redirects(client):
    response = client.post(
        "/admin/items/new",
        data={"title": "Couch", "description": "Blue", "price": "50.00", "status": "available"},
        follow_redirects=False,
    )
    assert response.status_code == 303


def test_created_item_appears_in_admin(client):
    client.post("/admin/items/new", data={"title": "Chair", "description": "", "price": "10.00", "status": "available"})
    response = client.get("/admin")
    assert "Chair" in response.text


def test_created_item_appears_in_catalog(client):
    client.post("/admin/items/new", data={"title": "Table", "description": "Oak", "price": "80.00", "status": "available"})
    response = client.get("/")
    assert "Table" in response.text


def test_edit_item_form_loads(client):
    client.post("/admin/items/new", data={"title": "Lamp", "description": "", "price": "5.00", "status": "available"})
    response = client.get("/admin/items/1/edit")
    assert response.status_code == 200
    assert "Lamp" in response.text


def test_update_item(client):
    client.post("/admin/items/new", data={"title": "Old Name", "description": "", "price": "5.00", "status": "available"})
    client.post("/admin/items/1/edit", data={"title": "New Name", "description": "", "price": "8.00", "status": "sold"})
    response = client.get("/admin")
    assert "New Name" in response.text


def test_delete_item(client):
    client.post("/admin/items/new", data={"title": "Gone", "description": "", "price": "1.00", "status": "available"})
    client.post("/admin/items/1/delete")
    response = client.get("/admin")
    assert "Gone" not in response.text


def test_item_detail_loads(client):
    client.post("/admin/items/new", data={"title": "Vase", "description": "Blue ceramic", "price": "45.00", "status": "available"})
    response = client.get("/items/1")
    assert response.status_code == 200
    assert "Vase" in response.text
    assert "Blue ceramic" in response.text
    assert "45.00" in response.text


def test_item_detail_404(client):
    response = client.get("/items/999")
    assert response.status_code == 404


def test_catalog_cards_link_to_detail(client):
    client.post("/admin/items/new", data={"title": "Mirror", "description": "", "price": "30.00", "status": "available"})
    response = client.get("/")
    assert 'href="/items/1"' in response.text


def test_api_requires_auth(client):
    response = client.get("/api/items")
    assert response.status_code == 401


def test_api_list_items(client):
    client.post("/admin/items/new", data={"title": "Chair", "description": "Oak", "price": "120.00", "status": "available"})
    response = client.get("/api/items", headers={"Authorization": "Bearer test"})
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Chair"
    assert data[0]["description"] == "Oak"


def test_api_get_item(client):
    client.post("/admin/items/new", data={"title": "Table", "description": "Pine", "price": "200.00", "status": "available"})
    response = client.get("/api/items/1", headers={"Authorization": "Bearer test"})
    assert response.status_code == 200
    assert response.json()["title"] == "Table"


def test_api_get_item_404(client):
    response = client.get("/api/items/999", headers={"Authorization": "Bearer test"})
    assert response.status_code == 404


def test_api_patch_item(client):
    client.post("/admin/items/new", data={"title": "Old Title", "description": "Old desc", "price": "50.00", "status": "available"})
    response = client.patch("/api/items/1", json={"title": "New Title", "description": "New desc"}, headers={"Authorization": "Bearer test"})
    assert response.status_code == 200
    assert response.json()["title"] == "New Title"
    assert response.json()["description"] == "New desc"


def test_api_patch_partial(client):
    client.post("/admin/items/new", data={"title": "Keep Me", "description": "Old desc", "price": "50.00", "status": "available"})
    response = client.patch("/api/items/1", json={"description": "Better desc"}, headers={"Authorization": "Bearer test"})
    assert response.status_code == 200
    assert response.json()["title"] == "Keep Me"
    assert response.json()["description"] == "Better desc"


def test_api_patch_404(client):
    response = client.patch("/api/items/999", json={"title": "X"}, headers={"Authorization": "Bearer test"})
    assert response.status_code == 404


def test_set_cover_image(client):
    client.post("/admin/items/new", data={"title": "Shelf", "description": "", "price": "20.00", "status": "available"})
    img_a = database.add_image(1, "a.jpg", sort_order=0)
    img_b = database.add_image(1, "b.jpg", sort_order=1)

    response = client.post(f"/admin/items/1/images/{img_b}/set-cover", follow_redirects=False)

    assert response.status_code == 303
    images = database.get_images(1)
    assert images[0]["id"] == img_b


def test_set_cover_image_wrong_image_returns_404(client):
    client.post("/admin/items/new", data={"title": "Bench", "description": "", "price": "15.00", "status": "available"})
    database.add_image(1, "a.jpg", sort_order=0)

    response = client.post("/admin/items/1/images/9999/set-cover", follow_redirects=False)

    assert response.status_code == 404


def test_set_cover_image_nonexistent_item_returns_404(client):
    response = client.post("/admin/items/999/images/1/set-cover", follow_redirects=False)

    assert response.status_code == 404
