#!/bin/bash
# Quick test of loco MCP server

set -e

echo "🧪 Testing loco MCP server..."
echo

# Test 1: Initialize
echo "Test 1: Initialize request"
INIT_REQUEST='{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}'
RESPONSE=$(echo "$INIT_REQUEST" | loco mcp-server 2>/dev/null | head -1)
echo "Request: $INIT_REQUEST"
echo "Response: $RESPONSE"
echo

# Test 2: List tools
echo "Test 2: List tools request"
LIST_REQUEST='{"jsonrpc":"2.0","id":2,"method":"tools/list","params":{}}'
# First initialize, then list
(echo "$INIT_REQUEST" && echo "$LIST_REQUEST") | loco mcp-server 2>/dev/null | tail -1 > /tmp/loco_mcp_test.json
RESPONSE=$(cat /tmp/loco_mcp_test.json)
echo "Request: $LIST_REQUEST"
echo "Response: $RESPONSE"
echo

# Verify response contains tools
if echo "$RESPONSE" | grep -q '"tools"'; then
    echo "✅ MCP server test passed!"
    exit 0
else
    echo "❌ MCP server test failed!"
    exit 1
fi
