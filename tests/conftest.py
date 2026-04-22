import pytest
import os
import database
from fastapi.testclient import TestClient


@pytest.fixture
def client(tmp_path):
    uploads = tmp_path / "uploads"
    uploads.mkdir()
    database.init_db(str(tmp_path / "test.db"))
    import main
    main.UPLOADS_DIR = str(uploads)
    return TestClient(main.app)
