"""
Test suite for Phase 38: Web UI & Visual Layout Inspector Studio (scandoc studio).
"""

from fastapi.testclient import TestClient
import pytest

from scandoc.cli import main
from scandoc.cli.parser import create_parser
from scandoc.server.app import create_app


@pytest.fixture
def client():
    app = create_app()
    return TestClient(app)


def test_studio_ui_endpoint(client):
    """Test GET /studio endpoint serving Visual Layout Inspector HTML UI."""
    response = client.get("/studio")
    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]
    assert "scanDOC Studio" in response.text
    assert "Visual Layout Bounding Boxes" in response.text


def test_studio_inspect_endpoint(client):
    """Test POST /api/studio/inspect converting document and producing bounding box overlays."""
    files = {"file": ("test.pdf", b"Sample PDF text content for studio layout inspection", "application/pdf")}
    response = client.post("/api/studio/inspect", files=files)
    
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    assert "markdown" in data
    assert "html" in data
    assert "pages" in data
    assert len(data["pages"]) >= 1
    
    p0 = data["pages"][0]
    assert "blocks" in p0
    assert len(p0["blocks"]) >= 1
    assert "bbox" in p0["blocks"][0]
    assert "color" in p0["blocks"][0]


def test_cli_studio_parser():
    """Test CLI parser parsing 'scandoc studio' arguments."""
    parser = create_parser()
    args = parser.parse_args(["studio", "--host", "127.0.0.1", "-p", "8000", "--no-browser"])
    
    assert args.command == "studio"
    assert args.host == "127.0.0.1"
    assert args.port == 8000
    assert args.open_browser is False
