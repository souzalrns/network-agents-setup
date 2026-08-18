export interface PlanStep {
  id: string;
  agentId: string;
  description: string;
  prompt?: string;
  contextKeys?: string[];
  critical?: boolean;
  temperature?: number;
  maxTokens?: number;
  dependsOn?: string[];
  requiresApproval?: boolean;
  approvalTitle?: string;
  approvalDescription?: string;
  approvalCategory?: string;
  approvalPriority?: string;
  approvalExpiresIn?: number;
  alternatives?: string[];
  risks?: string[];
  impacts?: string[];
  approvalMetadata?: Record<string, any>;
}
export interface Plan {
  id: string;
  intent: string;
  domain: string;
  steps: PlanStep[];
  finalConsolidator?: string;
  conversationId?: string;
  metadata?: {
    agentId?: string;
    totalEstimatedTokens?: number;
    priority?: 'high' | 'medium' | 'low';
  };
}
export interface ExecutionResult {
  success: boolean;
  steps: Array<{
    id: string;
    agentId: string;
    success: boolean;
    output: any;
    error?: string;
    timestamp: Date;
  }>;
  finalOutput: string;
  errors: string[];
  metadata: {
    totalSteps: number;
    completedSteps: number;
    failedSteps: number;
    startTime: Date;
    endTime?: Date;
    durationMs?: number;
    totalTokens?: number;
    totalCost?: number;
  };
}
