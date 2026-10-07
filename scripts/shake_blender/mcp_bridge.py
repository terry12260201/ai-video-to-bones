"""Actual MCP stdio server forwarding to the installed Blender MCP addon's socket bridge."""
import socket,json
from mcp.server.fastmcp import FastMCP
mcp=FastMCP('Beagle Blender MCP')
@mcp.tool()
def execute_blender_code(code:str)->dict:
    """Execute Python inside Blender through its existing MCP addon on localhost:9876."""
    with socket.create_connection(('127.0.0.1',9876),timeout=900) as sock:
        sock.sendall(json.dumps({'type':'execute','code':code,'strict_json':True}).encode()+b'\0')
        data=b''
        while b'\0' not in data:
            block=sock.recv(1048576)
            if not block:raise RuntimeError('Blender MCP connection closed before response')
            data+=block
    response=json.loads(data.split(b'\0')[0])
    if response.get('status')!='ok':raise RuntimeError(response.get('message',str(response)))
    return response
if __name__=='__main__':mcp.run(transport='stdio')
