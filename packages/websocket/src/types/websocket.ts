export interface WebSocketMessage {
  id: string;
  type: 'request' | 'response' | 'event' | 'error';
  action: string;
  payload: any;
  timestamp: Date;
  correlationId?: string;
}
export interface WebSocketConnection {
  id: string;
  userId?: string;
  rooms: Set<string>;
  isAuthenticated: boolean;
  connectedAt: Date;
  lastActivity: Date;
  metadata: Record<string, any>;
}
export interface WebSocketRoom {
  id: string;
  name: string;
  connections: Set<string>;
  metadata: Record<string, any>;
}
export enum WebSocketAction {
  CHAT_SEND = 'chat:send',
  CHAT_STREAM = 'chat:stream',
  CHAT_HISTORY = 'chat:history',
  EXECUTION_START = 'execution:start',
  EXECUTION_STATUS = 'execution:status',
  EXECUTION_CANCEL = 'execution:cancel',
  EXECUTION_STEPS = 'execution:steps',
  HITL_LIST = 'hitl:list',
  HITL_APPROVE = 'hitl:approve',
  HITL_REJECT = 'hitl:reject',
  HITL_SUBSCRIBE = 'hitl:subscribe',
  AGENT_LIST = 'agent:list',
  AGENT_DETAIL = 'agent:detail',
  AGENT_EXECUTE = 'agent:execute',
  SYSTEM_STATUS = 'system:status',
  SYSTEM_METRICS = 'system:metrics',
  SYSTEM_HEALTH = 'system:health',
}
