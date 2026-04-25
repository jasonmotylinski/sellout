import base64
import pytest
import database
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    database.init_db(str(tmp_path / "test.db"))
    import main
    main.UPLOADS_DIR = str(uploads)
    main.ADMIN_USER = "test"
    main.ADMIN_PASS = "test"
    main.API_KEY = "test"
    token = base64.b64encode(b"test:test").decode()
    return TestClient(main.app, headers={"Authorization": f"Basic {token}"})
