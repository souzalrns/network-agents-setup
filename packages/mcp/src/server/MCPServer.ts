import { Request, Response } from 'express';
import { MCPTool, MCPToolResult, MCPServer as IMCPServer } from '../types/mcp';
import { ToolRegistry } from '../tools/ToolRegistry';
import { ToolExecutor } from '../tools/ToolExecutor';
export class MCPServer implements IMCPServer {
  private registry: ToolRegistry;
  private executor: ToolExecutor;
  constructor(tools: MCPTool[] = []) {
    this.registry = new ToolRegistry(tools);
    this.executor = new ToolExecutor(this.registry);
  }
  getTools(): MCPTool[] {
    return this.registry.listTools();
  }
  async executeTool(name: string, params: Record<string, any>): Promise<MCPToolResult> {
    return this.executor.executeTool(name, params);
  }
  registerTools(tools: MCPTool[]): void {
    for (const tool of tools) {
      this.registry.registerTool(tool);
    }
  }
  // Para integração com OpenAI/Anthropic
  getToolsForLLM(): any[] {
    return this.registry.getToolsForLLM();
  }
  // Para servir via HTTP/SSE (para clientes MCP)
  createHttpHandler() {
    return async (req: Request, res: Response) => {
      const { method, params } = req.body;
      
      if (method === 'getTools') {
        res.json({ tools: this.getTools() });
        return;
      }
      
      if (method === 'executeTool') {
        const result = await this.executeTool(params.name, params.params);
        res.json(result);
        return;
      }
      
      res.status(400).json({ error: 'Invalid method' });
    };
  }
}
