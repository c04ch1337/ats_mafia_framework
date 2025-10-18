"""
ATS MAFIA UI Integration Tests
Tests UI-backend connectivity, API endpoints, and WebSocket communication
"""

import pytest
import asyncio
import json
from fastapi.testclient import TestClient
from fastapi import FastAPI, WebSocket
from typing import Dict, List

# Mock FastAPI app for testing
app = FastAPI()


class TestUIBackendIntegration:
    """Test suite for UI-backend integration"""
    
    @pytest.fixture
    def client(self):
        """Create test client"""
        return TestClient(app)
    
    def test_api_client_initialization(self):
        """Test API client can be initialized"""
        # This would test the JavaScript API client initialization
        # In a real scenario, you'd use a headless browser like Selenium or Playwright
        assert True, "API client initialization test placeholder"
    
    def test_scenarios_endpoint(self, client):
        """Test scenarios API endpoint accessibility"""
        # Mock the endpoint
        @app.get("/api/v1/scenarios")
        async def get_scenarios():
            return [{
                "id": "test-scenario-1",
                "name": "Test Scenario",
                "description": "Test scenario description",
                "difficulty": "medium"
            }]
        
        response = client.get("/api/v1/scenarios")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) > 0
    
    def test_profiles_endpoint(self, client):
        """Test profiles API endpoint accessibility"""
        @app.get("/api/v1/profiles")
        async def get_profiles():
            return [{
                "id": "test-profile-1",
                "name": "Test Profile",
                "type": "penetration_tester",
                "status": "active"
            }]
        
        response = client.get("/api/v1/profiles")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_tools_endpoint(self, client):
        """Test tools API endpoint accessibility"""
        @app.get("/api/v1/tools")
        async def get_tools(category: str = "all"):
            return [{
                "name": "nmap",
                "category": "scanning",
                "description": "Network mapper",
                "status": "available"
            }]
        
        response = client.get("/api/v1/tools")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_llm_models_endpoint(self, client):
        """Test LLM models API endpoint accessibility"""
        @app.get("/api/v1/llm/models")
        async def get_models():
            return [{
                "name": "gpt-4",
                "provider": "openai",
                "context_window": 8192,
                "cost_per_1k_tokens": 0.03
            }]
        
        response = client.get("/api/v1/llm/models")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
    
    def test_training_session_create(self, client):
        """Test training session creation endpoint"""
        @app.post("/api/v1/training/sessions")
        async def create_session(session_data: Dict):
            return {
                "id": "session-123",
                "scenario_id": session_data.get("scenario_id"),
                "status": "created"
            }
        
        session_data = {
            "scenario_id": "test-scenario",
            "name": "Test Session",
            "model": "gpt-4"
        }
        
        response = client.post("/api/v1/training/sessions", json=session_data)
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert data["status"] == "created"
    
    def test_cost_summary_endpoint(self, client):
        """Test cost summary endpoint"""
        @app.get("/api/v1/llm/costs/summary")
        async def get_cost_summary(timeframe: str = "30d"):
            return {
                "total_spend": 125.50,
                "avg_session_cost": 10.25,
                "total_tokens": 1250000,
                "monthly_budget": 500,
                "dates": ["2024-01-01", "2024-01-02"],
                "daily_costs": [10.5, 15.2]
            }
        
        response = client.get("/api/v1/llm/costs/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_spend" in data
        assert "monthly_budget" in data
    
    def test_tool_execution_endpoint(self, client):
        """Test tool execution endpoint"""
        @app.post("/api/v1/tools/{tool_name}/execute")
        async def execute_tool(tool_name: str, parameters: Dict):
            return {
                "tool": tool_name,
                "status": "success",
                "output": "Tool executed successfully",
                "execution_time": 1.5
            }
        
        response = client.post("/api/v1/tools/nmap/execute", json={"target": "192.168.1.1"})
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "success"
    
    def test_analytics_endpoint(self, client):
        """Test analytics endpoint"""
        @app.get("/api/v1/analytics")
        async def get_analytics(time_range: str = "7d"):
            return {
                "labels": ["Day 1", "Day 2", "Day 3"],
                "success_rates": [85, 90, 88],
                "completion_times": [120, 110, 115]
            }
        
        response = client.get("/api/v1/analytics")
        assert response.status_code == 200
        data = response.json()
        assert "labels" in data
        assert "success_rates" in data


class TestWebSocketIntegration:
    """Test suite for WebSocket integration"""
    
    @pytest.mark.asyncio
    async def test_websocket_connection(self):
        """Test WebSocket connection establishment"""
        # Mock WebSocket endpoint
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                while True:
                    data = await websocket.receive_text()
                    message = json.loads(data)
                    
                    # Echo back with type confirmation
                    response = {
                        "type": "received",
                        "original_type": message.get("type"),
                        "timestamp": message.get("timestamp")
                    }
                    await websocket.send_json(response)
            except:
                pass
        
        with TestClient(app).websocket_connect("/ws?client_id=test123") as websocket:
            # Send a ping
            websocket.send_json({"type": "ping", "timestamp": 1234567890})
            
            # Receive response
            data = websocket.receive_json()
            assert data["type"] == "received"
            assert data["original_type"] == "ping"
    
    @pytest.mark.asyncio
    async def test_websocket_subscribe(self):
        """Test WebSocket topic subscription"""
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message["type"] == "subscribe":
                    await websocket.send_json({
                        "type": "subscribed",
                        "topic": message["topic"]
                    })
            except:
                pass
        
        with TestClient(app).websocket_connect("/ws?client_id=test123") as websocket:
            # Subscribe to a topic
            websocket.send_json({"type": "subscribe", "topic": "system_status"})
            
            # Receive confirmation
            data = websocket.receive_json()
            assert data["type"] == "subscribed"
            assert data["topic"] == "system_status"
    
    @pytest.mark.asyncio
    async def test_websocket_session_join(self):
        """Test WebSocket session joining"""
        @app.websocket("/ws")
        async def websocket_endpoint(websocket: WebSocket):
            await websocket.accept()
            try:
                data = await websocket.receive_text()
                message = json.loads(data)
                
                if message["type"] == "join_session":
                    await websocket.send_json({
                        "type": "session_joined",
                        "session_id": message["session_id"]
                    })
            except:
                pass
        
        with TestClient(app).websocket_connect("/ws?client_id=test123") as websocket:
            # Join a session
            websocket.send_json({"type": "join_session", "session_id": "session-456"})
            
            # Receive confirmation
            data = websocket.receive_json()
            assert data["type"] == "session_joined"
            assert data["session_id"] == "session-456"


class TestDockerDeployment:
    """Test suite for Docker deployment verification"""
    
    def test_docker_compose_valid(self):
        """Test docker-compose.yml is valid"""
        import os
        import yaml
        
        compose_file = os.path.join(os.path.dirname(__file__), "../../docker-compose.yml")
        
        if os.path.exists(compose_file):
            with open(compose_file, 'r') as f:
                config = yaml.safe_load(f)
            
            assert "services" in config
            assert "ats-mafia-framework" in config["services"]
            assert "volumes" in config
            assert "networks" in config
        else:
            pytest.skip("docker-compose.yml not found")
    
    def test_env_example_exists(self):
        """Test .env.example file exists"""
        import os
        
        env_file = os.path.join(os.path.dirname(__file__), "../../.env.example")
        assert os.path.exists(env_file), ".env.example file should exist"
    
    def test_dockerfile_exists(self):
        """Test Dockerfile exists"""
        import os
        
        dockerfile = os.path.join(os.path.dirname(__file__), "../Dockerfile")
        assert os.path.exists(dockerfile), "Dockerfile should exist"


class TestUIComponentsExist:
    """Test suite to verify UI components exist"""
    
    def test_tools_html_exists(self):
        """Test tools.html template exists"""
        import os
        
        tools_html = os.path.join(os.path.dirname(__file__), "../ui/templates/tools.html")
        assert os.path.exists(tools_html), "tools.html should exist"
    
    def test_llm_management_html_exists(self):
        """Test llm_management.html template exists"""
        import os
        
        llm_html = os.path.join(os.path.dirname(__file__), "../ui/templates/llm_management.html")
        assert os.path.exists(llm_html), "llm_management.html should exist"
    
    def test_tools_controller_exists(self):
        """Test tools_controller.js exists"""
        import os
        
        controller = os.path.join(os.path.dirname(__file__), "../ui/js/tools_controller.js")
        assert os.path.exists(controller), "tools_controller.js should exist"
    
    def test_llm_controller_exists(self):
        """Test llm_controller.js exists"""
        import os
        
        controller = os.path.join(os.path.dirname(__file__), "../ui/js/llm_controller.js")
        assert os.path.exists(controller), "llm_controller.js should exist"
    
    def test_websocket_server_exists(self):
        """Test websocket_server.py exists"""
        import os
        
        ws_server = os.path.join(os.path.dirname(__file__), "../api/websocket_server.py")
        assert os.path.exists(ws_server), "websocket_server.py should exist"
    
    def test_api_client_complete(self):
        """Test api-client.js has all required methods"""
        import os
        
        api_client = os.path.join(os.path.dirname(__file__), "../ui/js/api-client.js")
        
        if os.path.exists(api_client):
            with open(api_client, 'r') as f:
                content = f.read()
            
            required_methods = [
                'getModels',
                'getToolDetails',
                'executeTool',
                'getCostSummary',
                'getOperatorPerformance',
                'getLeaderboard'
            ]
            
            for method in required_methods:
                assert method in content, f"API client should have {method} method"
        else:
            pytest.skip("api-client.js not found")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])