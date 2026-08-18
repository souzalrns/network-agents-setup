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
  agentId: string;
  domain: string;
  category: HitlCategory;
  priority: HitlPriority;
  status: HitlStatus;
  title: string;
  description: string;
  context: Record<string, any>;
  proposedAction: string;
  alternatives?: string[];
  risks?: string[];
  impacts?: string[];
  requestedAt: Date;
  expiresAt?: Date;
  respondedAt?: Date;
  response?: 'approved' | 'rejected';
  responseComment?: string;
  responderId?: string;
  metadata?: Record<string, any>;
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
