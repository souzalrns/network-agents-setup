import { MCPTool, MCPToolResult, MCPClient as IMCPClient } from '../types/mcp';
export class MCPClient implements IMCPClient {
  private serverUrl: string | null = null;
  private tools: MCPTool[] = [];
  async connect(serverUrl: string): Promise<void> {
    this.serverUrl = serverUrl;
    
    // Carrega as ferramentas disponíveis
    try {
      const response = await fetch(`${serverUrl}/tools`);
      if (!response.ok) {
        throw new Error(`Failed to get tools: ${response.statusText}`);
      }
      const data = await response.json();
      this.tools = data.tools || [];
      console.log(`[MCP Client] Connected to ${serverUrl}, loaded ${this.tools.length} tools`);
    } catch (error: any) {
      console.error(`[MCP Client] Failed to connect: ${error.message}`);
      throw error;
    }
  }
  async getTools(): Promise<MCPTool[]> {
    return this.tools;
  }
  async executeTool(name: string, params: Record<string, any>): Promise<MCPToolResult> {
    if (!this.serverUrl) {
      throw new Error('MCP Client not connected');
    }
    try {
      const response = await fetch(`${this.serverUrl}/execute`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ name, params }),
      });
      if (!response.ok) {
        throw new Error(`Failed to execute tool: ${response.statusText}`);
      }
      return await response.json();
    } catch (error: any) {
      return {
        content: [{ type: 'text', text: `MCP error: ${error.message}` }],
        isError: true,
      };
    }
  }
  async disconnect(): Promise<void> {
    this.serverUrl = null;
    this.tools = [];
    console.log('[MCP Client] Disconnected');
  }
}
