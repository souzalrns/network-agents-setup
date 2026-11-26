import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { SecurityManager } from '../security/SecurityManager';
import { CognitiveRepository } from '../knowledge/CognitiveRepository';
import { DataGovernance } from '../data/DataGovernance';

export interface ConsentRecord {
  id: string;
  userId: string;
  purpose: string;
  granted: boolean;
  grantedAt: Date;
  revokedAt?: Date;
  scope: string[];
  metadata: Record<string, any>;
}

export interface DataSubjectRequest {
  id: string;
  userId: string;
  type: 'access' | 'rectification' | 'erasure' | 'restriction' | 'portability' | 'objection';
  status: 'pending' | 'processing' | 'completed' | 'rejected';
  requestedAt: Date;
  processedAt?: Date;
  response?: string;
  metadata: Record<string, any>;
}

export interface AuditLog {
  id: string;
  timestamp: Date;
  userId: string;
  action: string;
  resource: string;
  details: Record<string, any>;
  ip?: string;
  status: 'success' | 'failure';
}

export class ComplianceManager extends EventEmitter {
  private logger = getGlobalLogger();
  private consentRecords: Map<string, ConsentRecord> = new Map();
  private dataRequests: Map<string, DataSubjectRequest> = new Map();
  private auditLogs: AuditLog[] = [];
  private dataRequestHandlers: Map<DataSubjectRequest['type'], (r: DataSubjectRequest) => Promise<string> | string> = new Map();

  constructor(
    _securityManager: SecurityManager,
    _cognitiveRepository: CognitiveRepository,
    private dataGovernance: DataGovernance
  ) {
    super();
    this.logger.info('[ComplianceManager] Initialized');
  }

  // ===== P-077: LGPD/GDPR =====

  /**
   * Registra consentimento (P-077)
   */
  recordConsent(userId: string, purpose: string, scope: string[]): ConsentRecord {
    const id = `consent_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const record: ConsentRecord = {
      id,
      userId,
      purpose,
      granted: true,
      grantedAt: new Date(),
      scope,
      metadata: {
        source: 'user',
        ip: 'unknown',
      },
    };

    this.consentRecords.set(id, record);
    this.logger.info(`[ComplianceManager] Consent recorded: ${id}`);
    this.emit('consent:recorded', record);

    return record;
  }

  /**
   * Revoga consentimento (P-077)
   */
  revokeConsent(consentId: string): ConsentRecord {
    const record = this.consentRecords.get(consentId);
    if (!record) {
      throw new Error(`Consent ${consentId} not found`);
    }

    record.granted = false;
    record.revokedAt = new Date();
    this.consentRecords.set(consentId, record);

    this.logger.info(`[ComplianceManager] Consent revoked: ${consentId}`);
    this.emit('consent:revoked', record);

    return record;
  }

  /**
   * Verifica consentimento
   */
  checkConsent(userId: string, purpose: string): boolean {
    const records = Array.from(this.consentRecords.values())
      .filter((r) => r.userId === userId && r.purpose === purpose);

    const active = records.filter((r) => r.granted && !r.revokedAt);
    return active.length > 0;
  }

  /**
   * Solicitação de dados (P-077)
   */
  requestDataAccess(
    userId: string,
    type: DataSubjectRequest['type']
  ): DataSubjectRequest {
    const id = `dsr_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`;

    const request: DataSubjectRequest = {
      id,
      userId,
      type,
      status: 'pending',
      requestedAt: new Date(),
      metadata: {
        source: 'user',
      },
    };

    this.dataRequests.set(id, request);
    this.logger.info(`[ComplianceManager] Data request: ${id} (${type})`);
    this.emit('datarequest:created', request);

    // Processa já; sem executor registado fica pendente (ver registerDataRequestHandler)
    void this.processDataRequest(id);

    return request;
  }

  /**
   * Regista quem executa de verdade um tipo de pedido do titular (apagar, exportar, retificar...).
   * Sem executor registado o pedido NÃO é dado como concluído: fica `pending` à espera de tratamento manual.
   */
  registerDataRequestHandler(
    type: DataSubjectRequest['type'],
    handler: (request: DataSubjectRequest) => Promise<string> | string
  ): void {
    this.dataRequestHandlers.set(type, handler);
  }

  /**
   * Processa solicitação de dados (P-077). Só marca `completed` se um executor real correu sem erro.
   */
  async processDataRequest(requestId: string): Promise<DataSubjectRequest | undefined> {
    const request = this.dataRequests.get(requestId);
    if (!request) return undefined;

    const handler = this.dataRequestHandlers.get(request.type);
    if (!handler) {
      request.response = `Sem executor registado para "${request.type}": tratar manualmente. Nada foi alterado.`;
      this.dataRequests.set(requestId, request);
      this.logger.warn(`[ComplianceManager] Data request ${requestId} (${request.type}) sem executor: fica pendente`);
      this.emit('datarequest:manual', request);
      return request;
    }

    request.status = 'processing';
    this.dataRequests.set(requestId, request);
    try {
      request.response = await handler(request);
      request.status = 'completed';
      request.processedAt = new Date();
      this.logger.info(`[ComplianceManager] Data request completed: ${requestId}`);
      this.emit('datarequest:completed', request);
    } catch (err) {
      request.status = 'pending';
      request.response = `Falhou: ${err instanceof Error ? err.message : String(err)}. Nada foi dado como concluído.`;
      this.logger.error(`[ComplianceManager] Data request ${requestId} falhou`);
      this.emit('datarequest:failed', request);
    }
    this.dataRequests.set(requestId, request);
    return request;
  }

  // ===== P-078: Auditoria =====

  /**
   * Registra evento de auditoria (P-078)
   */
  logAudit(data: {
    userId: string;
    action: string;
    resource: string;
    details: Record<string, any>;
    ip?: string;
    status: 'success' | 'failure';
  }): AuditLog {
    const log: AuditLog = {
      id: `audit_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date(),
      ...data,
    };

    this.auditLogs.push(log);
    this.logger.info(`[ComplianceManager] Audit log: ${log.id} (${data.action})`);
    this.emit('audit:logged', log);

    // Limita tamanho do log
    if (this.auditLogs.length > 10000) {
      this.auditLogs = this.auditLogs.slice(-5000);
    }

    return log;
  }

  /**
   * Obtém logs de auditoria
   */
  getAuditLogs(filters?: {
    userId?: string;
    action?: string;
    startDate?: Date;
    endDate?: Date;
    status?: 'success' | 'failure';
  }): AuditLog[] {
    let logs = this.auditLogs;

    if (filters) {
      if (filters.userId) {
        logs = logs.filter((l) => l.userId === filters.userId);
      }
      if (filters.action) {
        logs = logs.filter((l) => l.action === filters.action);
      }
      if (filters.status) {
        logs = logs.filter((l) => l.status === filters.status);
      }
      if (filters.startDate) {
        logs = logs.filter((l) => l.timestamp >= filters.startDate!);
      }
      if (filters.endDate) {
        logs = logs.filter((l) => l.timestamp <= filters.endDate!);
      }
    }

    return logs;
  }

  /**
   * Auditoria contínua de segurança (P-078)
   */
  async continuousSecurityAudit(): Promise<{
    passed: boolean;
    issues: string[];
    recommendations: string[];
    score: number;
  }> {
    this.logger.info('[ComplianceManager] Running continuous security audit');

    const issues: string[] = [];
    const recommendations: string[] = [];
    let score = 100;

    // Verifica consentimentos
    const consents = Array.from(this.consentRecords.values());
    const activeConsents = consents.filter((c) => c.granted && !c.revokedAt);
    if (activeConsents.length === 0) {
      issues.push('Nenhum consentimento ativo registrado');
      recommendations.push('Registrar consentimentos dos usuários');
      score -= 20;
    }

    // Verifica solicitações de dados
    const dataRequests = Array.from(this.dataRequests.values());
    const pendingRequests = dataRequests.filter((r) => r.status === 'pending');
    if (pendingRequests.length > 0) {
      issues.push(`${pendingRequests.length} solicitações de dados pendentes`);
      recommendations.push('Processar solicitações de dados pendentes');
      score -= 10;
    }

    // Verifica logs de auditoria
    const recentLogs = this.auditLogs.filter(
      (l) => Date.now() - l.timestamp.getTime() < 24 * 60 * 60 * 1000
    );
    if (recentLogs.length === 0) {
      // Nota de fidelidade: no material original esta linha referenciava uma
      // variável `warnings` inexistente (erro de compilação real, TS2304).
      // O padrão do restante do método é acumular em `issues`, então a
      // ocorrência foi corrigida para `issues.push(...)`.
      issues.push('Nenhum log de auditoria nas últimas 24 horas');
      score -= 5;
    }

    // Verifica conformidade com LGPD/GDPR
    const complianceCheck = this.checkCompliance();
    if (!complianceCheck.passed) {
      issues.push('Não conformidade com LGPD/GDPR');
      recommendations.push(...complianceCheck.recommendations);
      score -= 30;
    }

    this.emit('audit:security_completed', { score, issues, recommendations });

    return {
      passed: score >= 70,
      issues,
      recommendations,
      score: Math.max(0, score),
    };
  }

  /**
   * Verifica conformidade geral
   */
  private checkCompliance(): {
    passed: boolean;
    recommendations: string[];
  } {
    const recommendations: string[] = [];

    // Verifica dados minimizados
    const assets = this.dataGovernance.listAssets();
    const minimized = assets.filter((a) => a.size < 1000);
    if (minimized.length < assets.length * 0.5) {
      recommendations.push('Minimizar dados armazenados');
    }

    // Verifica transparência
    const hasTransparency = assets.some((a) => a.metadata.transparency);
    if (!hasTransparency) {
      recommendations.push('Implementar transparência de dados');
    }

    return {
      passed: recommendations.length === 0,
      recommendations,
    };
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalConsents: number;
    activeConsents: number;
    totalDataRequests: number;
    completedDataRequests: number;
    totalAuditLogs: number;
    complianceScore: number;
  } {
    const consents = Array.from(this.consentRecords.values());
    const requests = Array.from(this.dataRequests.values());

    return {
      totalConsents: consents.length,
      activeConsents: consents.filter((c) => c.granted && !c.revokedAt).length,
      totalDataRequests: requests.length,
      completedDataRequests: requests.filter((r) => r.status === 'completed').length,
      totalAuditLogs: this.auditLogs.length,
      complianceScore: this.computeScore(requests, this.auditLogs),
    };
  }

  /** Média de (pedidos do titular concluídos / total) e (auditorias com sucesso / total), em %; 100 se não há dados. */
  private computeScore(requests: DataSubjectRequest[], logs: AuditLog[]): number {
    const req = requests.length ? requests.filter((r) => r.status === 'completed').length / requests.length : 1;
    const aud = logs.length ? logs.filter((l) => l.status === 'success').length / logs.length : 1;
    return Math.round(((req + aud) / 2) * 100);
  }
}
