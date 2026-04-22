import pytest
import tempfile
import os
import database


@pytest.fixture(autouse=True)
def fresh_db(tmp_path):
    database.init_db(str(tmp_path / "test.db"))


def test_create_and_get_item():
    item_id = database.create_item(title="Couch", description="Blue sofa", price=50.0, status="available")
    item = database.get_item(item_id)
    assert item["title"] == "Couch"
    assert item["price"] == 50.0
    assert item["status"] == "available"


def test_list_items():
    database.create_item(title="Chair", description="", price=10.0, status="available")
    database.create_item(title="Table", description="", price=20.0, status="sold")
    items = database.list_items()
    assert len(items) == 2


def test_update_item():
    item_id = database.create_item(title="Lamp", description="", price=5.0, status="available")
    database.update_item(item_id, title="Floor Lamp", description="Tall", price=8.0, status="sold")
    item = database.get_item(item_id)
    assert item["title"] == "Floor Lamp"
    assert item["status"] == "sold"


def test_delete_item():
    item_id = database.create_item(title="Box", description="", price=1.0, status="available")
    database.delete_item(item_id)
    assert database.get_item(item_id) is None


def test_add_and_get_images():
    item_id = database.create_item(title="Desk", description="", price=30.0, status="available")
    database.add_image(item_id, filename="abc123.jpg", sort_order=0)
    database.add_image(item_id, filename="def456.jpg", sort_order=1)
    images = database.get_images(item_id)
    assert len(images) == 2
    assert images[0]["filename"] == "abc123.jpg"


def test_delete_image():
    item_id = database.create_item(title="Shelf", description="", price=15.0, status="available")
    img_id = database.add_image(item_id, filename="img.jpg", sort_order=0)
    database.delete_image(img_id)
    assert database.get_images(item_id) == []


def test_delete_item_cascades_images():
    item_id = database.create_item(title="Wardrobe", description="", price=100.0, status="available")
    database.add_image(item_id, filename="img.jpg", sort_order=0)
    database.delete_item(item_id)
    assert database.get_images(item_id) == []
