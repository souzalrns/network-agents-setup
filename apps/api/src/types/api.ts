export interface ChatRequest {
  message: string;
  domain?: string;
  context?: Record<string, any>;
  stream?: boolean;
}
export interface ChatResponse {
  executionId: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  result?: string;
  steps?: any[];
  errors?: string[];
  metadata?: {
    totalSteps: number;
    completedSteps: number;
    failedSteps: number;
    durationMs?: number;
    totalTokens?: number;
    cost?: number;
  };
}
export interface ExecutionStatus {
  id: string;
  status: 'pending' | 'running' | 'completed' | 'failed' | 'cancelled' | 'waiting_hitl';
  domain: string;
  intent: string;
  startedAt: Date;
  updatedAt: Date;
  completedAt?: Date;
  progress: number;
  currentStep?: string;
  result?: string;
  errors?: string[];
  steps: Array<{
    id: string;
    agentId: string;
    description: string;
    status: 'pending' | 'running' | 'completed' | 'failed' | 'blocked';
    output?: any;
    error?: string;
    startedAt?: Date;
    completedAt?: Date;
  }>;
}
export interface AgentInfo {
  id: string;
  name: string;
  layer: 'meta' | 'horizontal' | 'vertical' | 'personal';
  visibility: 'public' | 'private';
  domain?: string;
  description: string;
  capabilities: string[];
  tools?: string[];
}
export interface HitlPendingRequest {
  id: string;
  agentId: string;
  domain: string;
  priority: string;
  category: string;
  title: string;
  description: string;
  proposedAction: string;
  alternatives?: string[];
  risks?: string[];
  impacts?: string[];
  requestedAt: Date;
  expiresAt?: Date;
}
export interface Metrics {
  totalExecutions: number;
  successfulExecutions: number;
  failedExecutions: number;
  averageDurationMs: number;
  totalTokens: number;
  totalCost: number;
  agentsUsage: Array<{
    agentId: string;
    calls: number;
    totalTokens: number;
    totalCost: number;
    averageDurationMs: number;
  }>;
  hitl: {
    pending: number;
    approved: number;
    rejected: number;
    expired: number;
  };
}
