import { ToolRegistry, MCPTool, MCPToolResult } from './ToolRegistry';
export class ToolExecutor {
  constructor(private registry: ToolRegistry) {}
  async executeTool(name: string, params: Record<string, any>): Promise<MCPToolResult> {
    const tool = this.registry.getTool(name);
    if (!tool) {
      return { content: [{ type: 'text', text: `Tool ${name} not found` }], isError: true };
    }
    try {
      this.validateParams(tool, params);
      return await tool.execute(params);
    } catch (error: any) {
      return { content: [{ type: 'text', text: `Error: ${error.message}` }], isError: true };
    }
  }
  private validateParams(tool: MCPTool, params: Record<string, any>): void {
    const required = tool.inputSchema.required || [];
    for (const field of required) {
      if (params[field] === undefined || params[field] === null) {
        throw new Error(`Missing required parameter: ${field}`);
      }
    }
  }
}
