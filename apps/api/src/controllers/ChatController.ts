import { Request, Response } from 'express';
import { Orchestrator } from '@network-agents/core';
import { ExecutionService } from '../services/ExecutionService';
import { v4 as uuidv4 } from 'uuid';
export class ChatController {
  constructor(
    private orchestrator: Orchestrator,
    private executionService: ExecutionService
  ) {}
  async processChat(req: Request, res: Response): Promise<void> {
    const { message, domain, context, stream = false } = req.body;
    if (!message) {
      res.status(400).json({ error: 'message is required' });
      return;
    }
    const executionId = uuidv4();
    try {
      if (stream) {
        await this.processChatStream(executionId, message, domain, context, res);
        return;
      }
      const result = await this.orchestrator.processRequest(message, {
        domain,
        ...context,
        executionId,
      });
      res.json({
        executionId,
        status: 'completed',
        result: result.content,
        metadata: result.metadata,
      });
    } catch (error: any) {
      res.status(500).json({
        executionId,
        status: 'failed',
        errors: [error.message],
      });
    }
  }
  /**
   * Consulta o status de uma execução de chat previamente iniciada.
   */
  async getChatStatus(req: Request, res: Response): Promise<void> {
    const { executionId } = req.params;
    const execution = await this.executionService.getExecution(executionId);
    if (!execution) {
      res.status(404).json({ error: 'Execution not found' });
      return;
    }
    res.json(execution);
  }
  private async processChatStream(
    executionId: string,
    message: string,
    domain: string | undefined,
    context: Record<string, any> | undefined,
    res: Response
  ): Promise<void> {
    res.setHeader('Content-Type', 'text/event-stream');
    res.setHeader('Cache-Control', 'no-cache');
    res.setHeader('Connection', 'keep-alive');
    const sendEvent = (event: string, data: any) => {
      res.write(`event: ${event}\n`);
      res.write(`data: ${JSON.stringify(data)}\n\n`);
    };
    try {
      sendEvent('start', { executionId, message });
      await this.orchestrator.processRequestWithProgress(
        message,
        { domain, ...context, executionId },
        {
          onStepStart: (step) => sendEvent('step-start', step),
          onStepComplete: (step, result) => sendEvent('step-complete', { step, result }),
          onStepError: (error) => sendEvent('step-error', error),
          onComplete: (result) => sendEvent('complete', result),
          onError: (error) => sendEvent('error', { message: error.message }),
        }
      );
    } catch (error: any) {
      sendEvent('error', { message: error.message });
    } finally {
      res.end();
    }
  }
}
