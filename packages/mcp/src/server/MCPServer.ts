import { Request, Response } from 'express';
import { MCPTool, MCPToolResult, MCPServer as IMCPServer } from '../types/mcp';
import { ToolRegistry } from '../tools/ToolRegistry';
import { ToolExecutor, ExecutionContext } from '../tools/ToolExecutor';
import { authenticateRequest } from './McpAuth';
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
  async executeTool(
    name: string,
    params: Record<string, any>,
    context: ExecutionContext = {}
  ): Promise<MCPToolResult> {
    return this.executor.executeTool(name, params, context);
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
      const auth = authenticateRequest(req.headers['authorization'] as string | undefined);
      if (!auth.ok) {
        const status = auth.reason === 'not_configured' ? 503 : 401;
        res.status(status).json({ error: auth.reason === 'not_configured' ? 'Service unavailable: authentication is not configured' : 'Unauthorized' });
        return;
      }
      const caller = auth.caller as string;
      const { method, params } = req.body;

      if (method === 'getTools') {
        res.json({ tools: this.getTools() });
        return;
      }

      if (method === 'executeTool') {
        const result = await this.executeTool(params.name, params.params, { caller });
        res.json(result);
        return;
      }

      res.status(400).json({ error: 'Invalid method' });
    };
  }
}
