// Tipos para TrustManager e Certification
export interface TrustMetrics {
  reliability: number; // 0-100
  stability: number; // 0-100
  compliance: number; // 0-100
  quality: number; // 0-100
  learningCapacity: number; // 0-100
  decisionQuality: number; // 0-100
}
export interface AutonomyBoundary {
  financialLimit: number;
  operationalScope: string[];
  legalRestrictions: string[];
  ethicalConstraints: string[];
  riskTolerance: 'low' | 'medium' | 'high';
  escalationThreshold: number;
}
export interface Competence {
  id: string;
  name: string;
  description: string;
  domain: string;
  trustLevel: 'level_0' | 'level_1' | 'level_2' | 'level_3' | 'level_4' | 'level_5';
  metrics: TrustMetrics;
  certifiedAt?: Date;
  expiresAt?: Date;
  lastEvaluation?: Date;
  status: 'proposed' | 'in_evaluation' | 'certified' | 'suspended' | 'revoked';
  evidence: string[];
  history: Array<{
    date: Date;
    action: string;
    result: string;
  }>;
}
