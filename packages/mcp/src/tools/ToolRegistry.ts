export interface MCPTool {
  name: string;
  description: string;
  inputSchema: {
    type: 'object';
    properties: Record<string, { type: string; description?: string; enum?: any[]; default?: any }>;
    required?: string[];
  };
  execute: (params: Record<string, any>) => Promise<MCPToolResult>;
}
export interface MCPToolResult {
  content: Array<{ type: 'text' | 'image' | 'resource'; text?: string; data?: string; mimeType?: string }>;
  isError?: boolean;
  metadata?: Record<string, any>;
}
export class ToolRegistry {
  private tools: Map<string, MCPTool> = new Map();
  constructor(initialTools: MCPTool[] = []) {
    for (const tool of initialTools) this.registerTool(tool);
  }
  registerTool(tool: MCPTool): void {
    this.tools.set(tool.name, tool);
  }
  unregisterTool(name: string): void {
    this.tools.delete(name);
  }
  getTool(name: string): MCPTool | undefined {
    return this.tools.get(name);
  }
  listTools(): MCPTool[] {
    return Array.from(this.tools.values());
  }
  getToolsForLLM(): any[] {
    return this.listTools().map((tool) => ({
      type: 'function',
      function: {
        name: tool.name,
        description: tool.description,
        parameters: tool.inputSchema,
      },
    }));
  }
}
