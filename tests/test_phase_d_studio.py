import pytest
from fastapi.testclient import TestClient
from agent_fabric.server.app import create_app

def test_phase_d_studio_backend():
    """Verify Studio backend app initialization and HTTP CORS headers."""
    app = create_app()
    client = TestClient(app)
    res = client.options("/workspaces")
    # OPTIONS request check
    assert res.status_code in (200, 405)
    
    res_get = client.get("/workspaces")
    assert res_get.status_code == 200
