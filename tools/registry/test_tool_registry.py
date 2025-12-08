"""
Comprehensive unit tests for ToolRegistry.

Target: >70% coverage for promotion to universal-agent-nexus@3.1.0
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import httpx

from universal_agent_nexus.runtime import ToolRegistry, ToolDefinition, get_registry


class TestToolDefinition:
    """Tests for ToolDefinition model."""

    def test_tool_definition_creation(self):
        """Test creating a tool definition with all fields."""
        tool = ToolDefinition(
            name="test_tool",
            description="A test tool",
            server_url="http://localhost:8000/mcp",
            server_name="test_server",
            input_schema={"type": "object", "properties": {"query": {"type": "string"}}}
        )
        assert tool.name == "test_tool"
        assert tool.description == "A test tool"
        assert tool.server_url == "http://localhost:8000/mcp"
        assert tool.server_name == "test_server"
        assert tool.protocol == "mcp"  # Default value
        assert tool.input_schema == {"type": "object", "properties": {"query": {"type": "string"}}}

    def test_tool_definition_default_protocol(self):
        """Test that protocol defaults to 'mcp'."""
        tool = ToolDefinition(
            name="test",
            description="Test",
            server_url="http://localhost:8000/mcp",
            server_name="test",
            input_schema={}
        )
        assert tool.protocol == "mcp"

    def test_tool_definition_custom_protocol(self):
        """Test setting a custom protocol."""
        tool = ToolDefinition(
            name="test",
            description="Test",
            server_url="http://localhost:8000/mcp",
            server_name="test",
            input_schema={},
            protocol="custom"
        )
        assert tool.protocol == "custom"


class TestToolRegistry:
    """Tests for ToolRegistry class."""

    def test_initialization(self):
        """Test that registry initializes with empty state."""
        registry = ToolRegistry()
        assert len(registry.list_tools()) == 0
        assert len(registry.list_servers()) == 0

    def test_register_server(self):
        """Test registering a single server."""
        registry = ToolRegistry()
        registry.register_server("test_server", "http://localhost:8000/mcp")
        
        servers = registry.list_servers()
        assert "test_server" in servers
        assert servers["test_server"] == "http://localhost:8000/mcp"

    def test_register_multiple_servers(self):
        """Test registering multiple servers."""
        registry = ToolRegistry()
        registry.register_server("server1", "http://localhost:8000/mcp")
        registry.register_server("server2", "http://localhost:8001/mcp")
        registry.register_server("server3", "http://localhost:8002/mcp")
        
        servers = registry.list_servers()
        assert len(servers) == 3
        assert "server1" in servers
        assert "server2" in servers
        assert "server3" in servers

    def test_register_server_overwrites_existing(self):
        """Test that registering the same server name overwrites the URL."""
        registry = ToolRegistry()
        registry.register_server("test", "http://localhost:8000/mcp")
        registry.register_server("test", "http://localhost:9000/mcp")
        
        servers = registry.list_servers()
        assert servers["test"] == "http://localhost:9000/mcp"
        assert len(servers) == 1

    @patch("httpx.get")
    def test_discover_tools_success(self, mock_get):
        """Test successful tool discovery from a single server."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {
                    "name": "tool1",
                    "description": "First tool",
                    "inputSchema": {"type": "object"}
                },
                {
                    "name": "tool2",
                    "description": "Second tool",
                    "inputSchema": {"type": "object", "properties": {"x": {"type": "string"}}}
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        registry = ToolRegistry()
        registry.register_server("test", "http://localhost:8000/mcp")
        tools = registry.discover_tools()
        
        assert len(tools) == 2
        assert tools[0].name == "tool1"
        assert tools[0].description == "First tool"
        assert tools[0].server_name == "test"
        assert tools[0].server_url == "http://localhost:8000/mcp"
        assert tools[1].name == "tool2"
        
        # Verify tools are stored in registry
        assert registry.get_tool("tool1") is not None
        assert registry.get_tool("tool2") is not None

    @patch("httpx.get")
    def test_discover_tools_empty_response(self, mock_get):
        """Test discovery when server returns empty tools list."""
        mock_response = Mock()
        mock_response.json.return_value = {"tools": []}
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        registry = ToolRegistry()
        registry.register_server("test", "http://localhost:8000/mcp")
        tools = registry.discover_tools()
        
        assert len(tools) == 0

    @patch("httpx.get")
    def test_discover_tools_missing_description(self, mock_get):
        """Test discovery when tool definition lacks description."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {
                    "name": "tool_no_desc",
                    "inputSchema": {}
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        registry = ToolRegistry()
        registry.register_server("test", "http://localhost:8000/mcp")
        tools = registry.discover_tools()
        
        assert len(tools) == 1
        assert tools[0].name == "tool_no_desc"
        assert tools[0].description == ""  # Should default to empty string

    @patch("httpx.get")
    def test_discover_tools_missing_input_schema(self, mock_get):
        """Test discovery when tool definition lacks inputSchema."""
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {
                    "name": "tool_no_schema",
                    "description": "Tool without schema"
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        registry = ToolRegistry()
        registry.register_server("test", "http://localhost:8000/mcp")
        tools = registry.discover_tools()
        
        assert len(tools) == 1
        assert tools[0].input_schema == {}  # Should default to empty dict

    @patch("httpx.get")
    def test_discover_tools_http_error(self, mock_get):
        """Test discovery when server returns HTTP error."""
        mock_get.side_effect = httpx.HTTPStatusError(
            "Server error",
            request=Mock(),
            response=Mock(status_code=500)
        )
        
        registry = ToolRegistry()
        registry.register_server("test", "http://localhost:8000/mcp")
        
        # Should not raise, but return empty list and print warning
        tools = registry.discover_tools()
        assert len(tools) == 0

    @patch("httpx.get")
    def test_discover_tools_connection_error(self, mock_get):
        """Test discovery when server is unreachable."""
        mock_get.side_effect = httpx.ConnectError("Connection failed")
        
        registry = ToolRegistry()
        registry.register_server("test", "http://localhost:8000/mcp")
        
        # Should not raise, but return empty list
        tools = registry.discover_tools()
        assert len(tools) == 0

    @patch("httpx.get")
    def test_discover_tools_timeout(self, mock_get):
        """Test discovery when server times out."""
        mock_get.side_effect = httpx.TimeoutException("Request timed out")
        
        registry = ToolRegistry()
        registry.register_server("test", "http://localhost:8000/mcp")
        
        tools = registry.discover_tools()
        assert len(tools) == 0

    @patch("httpx.get")
    def test_discover_tools_specific_server(self, mock_get):
        """Test discovering tools from a specific server only."""
        # Mock response for first server
        mock_response1 = Mock()
        mock_response1.json.return_value = {
            "tools": [{"name": "tool1", "description": "Tool 1", "inputSchema": {}}]
        }
        mock_response1.raise_for_status = Mock()
        
        # Mock response for second server
        mock_response2 = Mock()
        mock_response2.json.return_value = {
            "tools": [{"name": "tool2", "description": "Tool 2", "inputSchema": {}}]
        }
        mock_response2.raise_for_status = Mock()
        
        mock_get.side_effect = [mock_response1, mock_response2]
        
        registry = ToolRegistry()
        registry.register_server("server1", "http://localhost:8000/mcp")
        registry.register_server("server2", "http://localhost:8001/mcp")
        
        # Discover from server1 only
        tools = registry.discover_tools(server_name="server1")
        
        assert len(tools) == 1
        assert tools[0].name == "tool1"
        assert tools[0].server_name == "server1"
        # Verify only one HTTP call was made
        assert mock_get.call_count == 1

    @patch("httpx.get")
    def test_discover_tools_nonexistent_server(self, mock_get):
        """Test discovering from a server that doesn't exist."""
        registry = ToolRegistry()
        registry.register_server("server1", "http://localhost:8000/mcp")
        
        # Try to discover from non-existent server - should raise KeyError
        # This matches the actual implementation behavior
        with pytest.raises(KeyError):
            registry.discover_tools(server_name="nonexistent")
        
        # Should not make any HTTP calls
        mock_get.assert_not_called()

    def test_get_tool_found(self):
        """Test getting a tool that exists."""
        registry = ToolRegistry()
        tool = ToolDefinition(
            name="test_tool",
            description="Test tool",
            server_url="http://localhost:8000/mcp",
            server_name="test",
            input_schema={}
        )
        registry._tools["test_tool"] = tool
        
        retrieved = registry.get_tool("test_tool")
        assert retrieved == tool
        assert retrieved.name == "test_tool"

    def test_get_tool_not_found(self):
        """Test getting a tool that doesn't exist."""
        registry = ToolRegistry()
        retrieved = registry.get_tool("nonexistent_tool")
        assert retrieved is None

    def test_list_tools_empty(self):
        """Test listing tools when registry is empty."""
        registry = ToolRegistry()
        tools = registry.list_tools()
        assert len(tools) == 0
        assert isinstance(tools, list)

    def test_list_tools_multiple(self):
        """Test listing multiple tools."""
        registry = ToolRegistry()
        tool1 = ToolDefinition(
            name="tool1", description="Tool 1",
            server_url="http://localhost:8000/mcp", server_name="test", input_schema={}
        )
        tool2 = ToolDefinition(
            name="tool2", description="Tool 2",
            server_url="http://localhost:8000/mcp", server_name="test", input_schema={}
        )
        registry._tools["tool1"] = tool1
        registry._tools["tool2"] = tool2
        
        tools = registry.list_tools()
        assert len(tools) == 2
        tool_names = [t.name for t in tools]
        assert "tool1" in tool_names
        assert "tool2" in tool_names

    def test_list_servers_empty(self):
        """Test listing servers when registry is empty."""
        registry = ToolRegistry()
        servers = registry.list_servers()
        assert len(servers) == 0
        assert isinstance(servers, dict)

    def test_list_servers_returns_copy(self):
        """Test that list_servers returns a copy, not the original dict."""
        registry = ToolRegistry()
        registry.register_server("test", "http://localhost:8000/mcp")
        
        servers1 = registry.list_servers()
        servers1["new_server"] = "http://localhost:9000/mcp"
        
        servers2 = registry.list_servers()
        # Original registry should not be modified
        assert "new_server" not in servers2
        assert len(servers2) == 1


class TestGetRegistry:
    """Tests for global registry singleton."""

    def test_singleton_pattern(self):
        """Test that get_registry returns the same instance."""
        registry1 = get_registry()
        registry2 = get_registry()
        assert registry1 is registry2

    def test_singleton_persistence(self):
        """Test that the singleton persists state across calls."""
        registry1 = get_registry()
        registry1.register_server("test", "http://localhost:8000/mcp")
        
        registry2 = get_registry()
        servers = registry2.list_servers()
        assert "test" in servers

    def test_singleton_independent_instances(self):
        """Test that creating new ToolRegistry() creates independent instances."""
        global_registry = get_registry()
        global_registry.register_server("global", "http://localhost:8000/mcp")
        
        local_registry = ToolRegistry()
        local_registry.register_server("local", "http://localhost:9000/mcp")
        
        # Global registry should not be affected
        global_servers = global_registry.list_servers()
        assert "local" not in global_servers
        assert "global" in global_servers
        
        # Local registry should be independent
        local_servers = local_registry.list_servers()
        assert "local" in local_servers
        assert "global" not in local_servers


class TestToolRegistryIntegration:
    """Integration tests for complete workflows."""

    @patch("httpx.get")
    def test_full_workflow(self, mock_get):
        """Test a complete workflow: register, discover, get, list."""
        # Setup mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "tools": [
                {
                    "name": "search_tool",
                    "description": "Search functionality",
                    "inputSchema": {"type": "object", "properties": {"query": {"type": "string"}}}
                },
                {
                    "name": "analyze_tool",
                    "description": "Analysis functionality",
                    "inputSchema": {"type": "object"}
                }
            ]
        }
        mock_response.raise_for_status = Mock()
        mock_get.return_value = mock_response
        
        # Execute workflow
        registry = ToolRegistry()
        
        # 1. Register server
        registry.register_server("api_server", "http://localhost:8000/mcp")
        assert len(registry.list_servers()) == 1
        
        # 2. Discover tools
        tools = registry.discover_tools()
        assert len(tools) == 2
        
        # 3. Get specific tool
        search_tool = registry.get_tool("search_tool")
        assert search_tool is not None
        assert search_tool.name == "search_tool"
        
        # 4. List all tools
        all_tools = registry.list_tools()
        assert len(all_tools) == 2
        assert all(tool.name in ["search_tool", "analyze_tool"] for tool in all_tools)

    @patch("httpx.get")
    def test_multiple_servers_discovery(self, mock_get):
        """Test discovering tools from multiple servers."""
        # Setup responses for two servers
        responses = [
            Mock(json=Mock(return_value={"tools": [{"name": "tool1", "description": "Tool 1", "inputSchema": {}}]}), raise_for_status=Mock()),
            Mock(json=Mock(return_value={"tools": [{"name": "tool2", "description": "Tool 2", "inputSchema": {}}]}), raise_for_status=Mock())
        ]
        mock_get.side_effect = responses
        
        registry = ToolRegistry()
        registry.register_server("server1", "http://localhost:8000/mcp")
        registry.register_server("server2", "http://localhost:8001/mcp")
        
        tools = registry.discover_tools()
        
        assert len(tools) == 2
        assert mock_get.call_count == 2
        # Verify tools are from different servers
        server_names = {tool.server_name for tool in tools}
        assert "server1" in server_names
        assert "server2" in server_names

