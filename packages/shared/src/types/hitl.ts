export enum HitlStatus {
  PENDING = 'pending',
  APPROVED = 'approved',
  REJECTED = 'rejected',
  EXPIRED = 'expired',
  CANCELLED = 'cancelled',
}
export enum HitlPriority {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical',
}
export enum HitlCategory {
  FINANCIAL = 'financial',
  LEGAL = 'legal',
  MEDICAL = 'medical',
  ARCHITECTURAL = 'architectural',
  CONTRACTUAL = 'contractual',
  STRATEGIC = 'strategic',
  SECURITY = 'security',
  APPROVAL = 'approval',
}
export interface HitlRequest {
  id: string;
  agentId: string | null;
  domain: string | null;
  category: HitlCategory | null;
  priority: HitlPriority;
  status: HitlStatus;
  title: string;
  description: string | null;
  context: Record<string, any>;
  proposedAction: string | null;
  alternatives?: string[];
  risks?: string[];
  impacts?: string[];
  requestedAt: Date;
  expiresAt?: Date;
  respondedAt?: Date;
  response?: 'approved' | 'rejected' | 'edit';
  responseComment?: string;
  responderId?: string;
  metadata?: Record<string, any>;
  /** Contrato v1 (hitl-request-v1.json) — presentes só em pedidos importados do plan_runner. */
  schema?: 'hitl-request-v1';
  source?: 'plan_runner' | 'node_api';
  runId?: string | null;
  planId?: string | null;
  stepId?: string | null;
  allow?: Array<'approve' | 'reject' | 'edit'>;
}
export interface HitlCheckpoint {
  id: string;
  hitlRequestId: string;
  planId: string;
  currentStepIndex: number;
  executionState: Record<string, any>;
  memorySnapshot: Record<string, any>;
  createdAt: Date;
  restoredAt?: Date;
}
