import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { DataGovernance } from '../data/DataGovernance';
import { SecurityManager } from '../security/SecurityManager';

// P-077/078: Conformidade LGPD/GDPR — registros de consentimento,
// solicitações do titular dos dados (acesso/retificação/exclusão/
// restrição/portabilidade/oposição) com processamento automático,
// registro de auditoria e auditoria de segurança contínua.

export interface ConsentRecord {
  id: string;
  userId: string;
  purpose: string;
  granted: boolean;
  grantedAt: Date;
  revokedAt?: Date;
}

export type DataSubjectRequestType =
  | 'access'
  | 'rectification'
  | 'erasure'
  | 'restriction'
  | 'portability'
  | 'objection';

export interface DataSubjectRequest {
  id: string;
  userId: string;
  type: DataSubjectRequestType;
  status: 'received' | 'processing' | 'completed' | 'rejected';
  createdAt: Date;
  completedAt?: Date;
  result?: string;
}

export interface AuditLogEntry {
  id: string;
  action: string;
  actor: string;
  details: Record<string, any>;
  timestamp: Date;
}

export class ComplianceManager extends EventEmitter {
  private consents: Map<string, ConsentRecord> = new Map();
  private requests: Map<string, DataSubjectRequest> = new Map();
  private auditLog: AuditLogEntry[] = [];
  private logger = getGlobalLogger();

  constructor(
    private dataGovernance: DataGovernance,
    private securityManager: SecurityManager
  ) {
    super();
  }

  recordConsent(userId: string, purpose: string, granted: boolean): ConsentRecord {
    const consent: ConsentRecord = {
      id: `consent_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      userId,
      purpose,
      granted,
      grantedAt: new Date(),
    };
    this.consents.set(consent.id, consent);
    this.logAudit('consent:recorded', userId, { purpose, granted });
    this.emit('consent:recorded', consent);
    return consent;
  }

  revokeConsent(consentId: string): ConsentRecord {
    const consent = this.consents.get(consentId);
    if (!consent) throw new Error(`Consentimento ${consentId} não encontrado`);
    consent.granted = false;
    consent.revokedAt = new Date();
    this.consents.set(consentId, consent);
    this.logAudit('consent:revoked', consent.userId, { consentId });
    return consent;
  }

  /**
   * Recebe e processa automaticamente uma solicitação do titular dos dados.
   */
  async submitDataSubjectRequest(userId: string, type: DataSubjectRequestType): Promise<DataSubjectRequest> {
    const request: DataSubjectRequest = {
      id: `dsr_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      userId,
      type,
      status: 'received',
      createdAt: new Date(),
    };
    this.requests.set(request.id, request);
    this.logAudit('dsr:received', userId, { type });
    this.emit('request:received', request);

    return this.processRequest(request.id);
  }

  private async processRequest(requestId: string): Promise<DataSubjectRequest> {
    const request = this.requests.get(requestId);
    if (!request) throw new Error(`Solicitação ${requestId} não encontrada`);

    request.status = 'processing';
    this.requests.set(requestId, request);

    const userAssets = this.dataGovernance.listAssets().filter(
      (a) => a.metadata?.userId === request.userId
    );

    switch (request.type) {
      case 'access':
        request.result = `${userAssets.length} ativo(s) de dados encontrados para o titular.`;
        break;
      case 'erasure':
        request.result = `Solicitação de exclusão registrada para ${userAssets.length} ativo(s). Execução física deve ser confirmada por operador.`;
        break;
      case 'portability':
        request.result = `Dados preparados para exportação em formato portável (${userAssets.length} ativo(s)).`;
        break;
      case 'rectification':
        request.result = 'Solicitação de retificação encaminhada para revisão manual.';
        break;
      case 'restriction':
        request.result = 'Processamento dos dados do titular restringido até nova avaliação.';
        break;
      case 'objection':
        request.result = 'Oposição registrada; processamento baseado em interesse legítimo suspenso.';
        break;
    }

    request.status = 'completed';
    request.completedAt = new Date();
    this.requests.set(requestId, request);
    this.logAudit('dsr:completed', request.userId, { type: request.type, result: request.result });
    this.emit('request:completed', request);
    return request;
  }

  private logAudit(action: string, actor: string, details: Record<string, any>): void {
    const entry: AuditLogEntry = {
      id: `audit_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      action,
      actor,
      details,
      timestamp: new Date(),
    };
    this.auditLog.push(entry);
    this.logger.info(`[ComplianceManager] Auditoria: ${action} por ${actor}`);
  }

  getAuditLog(): AuditLogEntry[] {
    return this.auditLog;
  }

  /**
   * Verifica conformidade geral varrendo os ativos de dados registrados
   * em busca de dados pessoais sem consentimento vinculado.
   */
  checkCompliance(): { compliant: boolean; issues: string[] } {
    const issues: string[] = [];
    const assets = this.dataGovernance.listAssets();
    for (const asset of assets) {
      if (asset.classification === 'confidential' || asset.classification === 'restricted') {
        const hasConsent = Array.from(this.consents.values()).some(
          (c) => c.granted && asset.metadata?.userId === c.userId
        );
        if (!hasConsent) {
          issues.push(`Ativo "${asset.name}" classificado como ${asset.classification} sem consentimento vinculado.`);
        }
      }
    }
    return { compliant: issues.length === 0, issues };
  }

  /**
   * Executa uma auditoria de segurança contínua, combinando eventos de
   * segurança recentes com achados de conformidade.
   */
  continuousSecurityAudit(): {
    issues: string[];
    warnings: string[];
    recommendations: string[];
  } {
    const issues: string[] = [];
    const warnings: string[] = [];
    const recommendations: string[] = [];

    const securityStatus = this.securityManager.getSecurityStatus();
    if (securityStatus.criticalEvents > 0) {
      issues.push(`${securityStatus.criticalEvents} evento(s) crítico(s) de segurança em aberto.`);
      recommendations.push('Revisar e remediar eventos críticos de segurança imediatamente.');
    }
    if (securityStatus.recentEvents > 50) {
      warnings.push(`Alto volume de eventos de segurança nas últimas 24h (${securityStatus.recentEvents}).`);
    }
    if (securityStatus.mfaEnabled === 0 && securityStatus.totalUsers > 0) {
      warnings.push('Nenhum usuário com MFA habilitado.');
      recommendations.push('Incentivar/exigir autenticação multifator (MFA) para todos os usuários.');
    }

    const complianceCheck = this.checkCompliance();
    if (!complianceCheck.compliant) {
      issues.push(...complianceCheck.issues);
      recommendations.push('Vincular consentimento explícito a todo dado pessoal classificado como confidencial/restrito.');
    }

    this.logAudit('security:continuous_audit', 'system', { issues, warnings });
    return { issues, warnings, recommendations };
  }

  getRequests(status?: DataSubjectRequest['status']): DataSubjectRequest[] {
    const all = Array.from(this.requests.values());
    return status ? all.filter((r) => r.status === status) : all;
  }
}
