import { WebSocket, WebSocketServer as WSServer } from 'ws';
import { EventEmitter } from 'events';
import { RoomManager } from './rooms/RoomManager';
import { WebSocketMessage } from './types/websocket';
import { randomUUID } from 'crypto';
import { getGlobalLogger } from '@network-agents/observability';
import { getGlobalMetrics } from '@network-agents/observability';
export class WebSocketServer extends EventEmitter {
  private wss: WSServer;
  private roomManager: RoomManager;
  private connections: Map<string, WebSocket> = new Map();
  private logger = getGlobalLogger();
  private metrics = getGlobalMetrics();
  constructor(server: any, options: { path?: string } = {}) {
    super();
    this.wss = new WSServer({ server, path: options.path || '/ws' });
    this.roomManager = new RoomManager();
    this.setup();
  }
  private setup(): void {
    this.wss.on('connection', (ws: WebSocket, req: any) => {
      const connectionId = randomUUID();
      const ip = req.socket?.remoteAddress || 'unknown';
      this.connections.set(connectionId, ws);
      this.roomManager.addConnection(connectionId, { ip });
      this.logger.info('WebSocket connection established', {
        connectionId,
        ip,
        totalConnections: this.connections.size,
      });
      this.metrics.gauge('websocket_connections', {}, this.connections.size);
      ws.on('message', async (data: Buffer) => {
        try {
          const message = JSON.parse(data.toString()) as WebSocketMessage;
          await this.handleMessage(connectionId, message);
        } catch (error: any) {
          this.logger.error('WebSocket message error', { connectionId, error: error.message });
          this.sendError(ws, 'Invalid message format', error.message);
        }
      });
      ws.on('close', () => {
        this.connections.delete(connectionId);
        this.roomManager.removeConnection(connectionId);
        this.logger.info('WebSocket connection closed', {
          connectionId,
          totalConnections: this.connections.size,
        });
        this.metrics.gauge('websocket_connections', {}, this.connections.size);
      });
      ws.on('error', (error: Error) => {
        this.logger.error('WebSocket connection error', { connectionId, error: error.message });
      });
      this.send(ws, {
        id: randomUUID(),
        type: 'event',
        action: 'system:connected',
        payload: { connectionId, timestamp: new Date(), totalConnections: this.connections.size },
        timestamp: new Date(),
      });
    });
    this.logger.info('WebSocket server started', { path: this.wss.options.path || '/ws' });
  }
  private async handleMessage(connectionId: string, message: WebSocketMessage): Promise<void> {
    const ws = this.connections.get(connectionId);
    if (!ws) throw new Error('Connection not found');
    this.roomManager.updateConnectionActivity(connectionId);
    this.emit('message', connectionId, message);
    this.emit(`action:${message.action}`, connectionId, message);
    // Roteamento de ações
    const handlers: Record<string, (data: any, callback: any) => Promise<void>> = {
      'chat:send': async (data, callback) => {
        const result = await this.emitAsync('chat:send', data);
        callback(result);
      },
      'chat:stream': async (data) => {
        this.emit('chat:stream', data);
      },
      'execution:start': async (data, callback) => {
        const result = await this.emitAsync('execution:start', data);
        callback(result);
      },
      'hitl:list': async (data, callback) => {
        const result = await this.emitAsync('hitl:list', data);
        callback(result);
      },
      'hitl:approve': async (data, callback) => {
        const result = await this.emitAsync('hitl:approve', data);
        callback(result);
      },
      'hitl:reject': async (data, callback) => {
        const result = await this.emitAsync('hitl:reject', data);
        callback(result);
      },
      'hitl:subscribe': async (data, callback) => {
        this.roomManager.joinRoom(connectionId, `hitl:${data.domain || 'all'}`);
        callback({ subscribed: true });
      },
      'agent:list': async (data, callback) => {
        const result = await this.emitAsync('agent:list', data);
        callback(result);
      },
      'system:status': async (data, callback) => {
        callback({
          status: 'healthy',
          connections: this.getActiveConnections(),
          rooms: this.roomManager.getConnectionStats(),
          uptime: process.uptime(),
          timestamp: new Date(),
        });
      },
      'system:metrics': async (data, callback) => {
        const result = await this.emitAsync('system:metrics', data);
        callback(result);
      },
    };
    const handler = handlers[message.action];
    if (!handler) {
      this.sendError(ws, 'Unknown action', `Action ${message.action} not found`);
      return;
    }
    try {
      await handler(message.payload, (result: any, error?: any) => {
        if (error) {
          this.sendError(ws, error.message);
          return;
        }
        this.send(ws, {
          id: randomUUID(),
          type: 'response',
          action: message.action,
          payload: result,
          timestamp: new Date(),
          correlationId: message.id,
        });
      });
    } catch (error: any) {
      this.sendError(ws, error.message);
    }
  }
  send(ws: WebSocket, message: WebSocketMessage): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify(message));
    }
  }
  sendError(ws: WebSocket, error: string, details?: string): void {
    if (ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({
        id: randomUUID(),
        type: 'error',
        action: 'system:error',
        payload: { error, details },
        timestamp: new Date(),
      }));
    }
  }
  broadcast(roomId: string, message: WebSocketMessage, exclude?: string): void {
    const connections = this.roomManager.getRoomConnections(roomId);
    for (const connectionId of connections) {
      if (connectionId === exclude) continue;
      const ws = this.connections.get(connectionId);
      if (ws && ws.readyState === WebSocket.OPEN) {
        this.send(ws, message);
      }
    }
  }
  broadcastToAll(message: WebSocketMessage): void {
    for (const [, ws] of this.connections) {
      if (ws.readyState === WebSocket.OPEN) {
        this.send(ws, message);
      }
    }
  }
  private async emitAsync(event: string, data: any): Promise<any> {
    return new Promise((resolve) => {
      this.emit(event, data, resolve);
    });
  }
  getActiveConnections(): number {
    return this.connections.size;
  }
  getConnectionStats(): any {
    return this.roomManager.getConnectionStats();
  }
  close(): void {
    this.wss.close();
    this.logger.info('WebSocket server closed');
  }
}
