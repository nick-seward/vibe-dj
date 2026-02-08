class TestRootEndpoints:
    """Test root and health check endpoints."""

    def test_root_endpoint(self, client):
        """Test root endpoint returns API information or UI."""
        response = client.get("/")
        assert response.status_code == 200

        # If UI dist exists, root serves HTML; otherwise serves JSON API info
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            data = response.json()
            assert data["name"] == "Vibe-DJ"
            assert "endpoints" in data
        elif "text/html" in content_type:
            # UI is being served, which is also valid
            assert len(response.content) > 0

    def test_health_check_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "status" in data
        assert "database" in data
        assert "faiss_index" in data
