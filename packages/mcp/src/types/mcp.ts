// Ferramenta MCP
export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, {
      type: string;
      description?: string;
      enum?: any[];
      default?: any;
    }>;
    required?: string[];
  };
  execute: (params: Record<string, any>) => Promise<MCPToolResult>;
}
// Resultado de uma ferramenta MCP
export interface MCPToolResult {
  content: Array<{
    type: 'text' | 'image' | 'resource';
    text?: string;
    data?: string;
    mimeType?: string;
  }>;
  isError?: boolean;
  metadata?: Record<string, any>;
}
// Registro de ferramentas
export interface MCPToolRegistry {
  tools: MCPTool[];
  getTool(name: string): MCPTool | undefined;
  registerTool(tool: MCPTool): void;
  unregisterTool(name: string): void;
  listTools(): MCPTool[];
}
// Servidor MCP
export interface MCPServer {
  getTools(): MCPTool[];
  executeTool(name: string, params: Record<string, any>): Promise<MCPToolResult>;
  registerTools(tools: MCPTool[]): void;
}
// Cliente MCP
export interface MCPClient {
  connect(serverUrl: string): Promise<void>;
  getTools(): Promise<MCPTool[]>;
  executeTool(name: string, params: Record<string, any>): Promise<MCPToolResult>;
  disconnect(): Promise<void>;
}
