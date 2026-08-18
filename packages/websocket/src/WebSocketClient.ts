import { EventEmitter } from 'events';
import WebSocket from 'ws';
import { WebSocketMessage } from './types/websocket';
import { randomUUID } from 'crypto';
export class WebSocketClient extends EventEmitter {
  private ws: WebSocket | null = null;
  private url: string;
  private reconnectAttempts: number = 0;
  private maxReconnectAttempts: number = 5;
  private reconnectDelay: number = 1000;
  private isConnected: boolean = false;
  constructor(url: string) {
    super();
    this.url = url;
  }
  connect(): Promise<void> {
    return new Promise((resolve, reject) => {
      this.ws = new WebSocket(this.url);
      this.ws.on('open', () => {
        this.isConnected = true;
        this.reconnectAttempts = 0;
        console.log('[WebSocket Client] Connected');
        resolve();
      });
      this.ws.on('message', (data: Buffer) => {
        try {
          const message = JSON.parse(data.toString()) as WebSocketMessage;
          this.handleMessage(message);
        } catch (error) {
          console.error('[WebSocket Client] Failed to parse message:', error);
        }
      });
      this.ws.on('close', () => {
        this.isConnected = false;
        console.log('[WebSocket Client] Disconnected');
        this.attemptReconnect();
      });
      this.ws.on('error', (error) => {
        console.error('[WebSocket Client] Error:', error);
        if (!this.isConnected) {
          reject(error);
        }
      });
    });
  }
  private handleMessage(message: WebSocketMessage): void {
    this.emit('message', message);
    this.emit(`action:${message.action}`, message);
    if (message.type === 'response') {
      this.emit(`response:${message.correlationId}`, message.payload);
    } else if (message.type === 'event') {
      this.emit(`event:${message.action}`, message.payload);
    }
  }
  private attemptReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[WebSocket Client] Max reconnect attempts reached');
      this.emit('error', new Error('Max reconnect attempts reached'));
      return;
    }
    this.reconnectAttempts++;
    const delay = this.reconnectDelay * Math.pow(2, this.reconnectAttempts - 1);
    console.log(`[WebSocket Client] Reconnecting in ${delay}ms (attempt ${this.reconnectAttempts})`);
    setTimeout(() => {
      this.connect().catch(() => {});
    }, delay);
  }
  send(action: string, payload: any): Promise<any> {
    return new Promise((resolve, reject) => {
      if (!this.ws || !this.isConnected) {
        reject(new Error('Not connected'));
        return;
      }
      const message: WebSocketMessage = {
        id: randomUUID(),
        type: 'request',
        action,
        payload,
        timestamp: new Date(),
      };
      const handler = (data: any) => {
        this.removeListener(`response:${message.id}`, handler);
        resolve(data);
      };
      this.once(`response:${message.id}`, handler);
      const timeout = setTimeout(() => {
        this.removeListener(`response:${message.id}`, handler);
        reject(new Error('Response timeout'));
      }, 30000);
      this.ws.send(JSON.stringify(message), (error) => {
        if (error) {
          clearTimeout(timeout);
          this.removeListener(`response:${message.id}`, handler);
          reject(error);
        }
      });
    });
  }
  // High-level APIs
  async chat(message: string, domain?: string, context?: Record<string, any>): Promise<any> {
    return this.send('chat:send', { message, domain, context });
  }
  async startExecution(message: string, domain?: string, context?: Record<string, any>): Promise<any> {
    return this.send('execution:start', { message, domain, context });
  }
  async listAgents(domain?: string): Promise<any> {
    return this.send('agent:list', { domain });
  }
  async listHitl(domain?: string): Promise<any> {
    return this.send('hitl:list', { domain });
  }
  async approveHitl(hitlId: string, comment?: string): Promise<any> {
    return this.send('hitl:approve', { hitlId, comment });
  }
  async rejectHitl(hitlId: string, comment?: string): Promise<any> {
    return this.send('hitl:reject', { hitlId, comment });
  }
  async subscribeHitl(domain?: string): Promise<any> {
    return this.send('hitl:subscribe', { domain });
  }
  disconnect(): void {
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }
  getStatus(): boolean {
    return this.isConnected;
  }
}
