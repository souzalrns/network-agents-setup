import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import crypto from 'crypto';
export interface User {
  id: string;
  email: string;
  name: string;
  role: 'admin' | 'user' | 'viewer' | 'agent';
  permissions: string[];
  mfaEnabled: boolean;
  mfaSecret?: string;
  createdAt: Date;
  lastLogin?: Date;
}
export interface Session {
  id: string;
  userId: string;
  token: string;
  expiresAt: Date;
  createdAt: Date;
  ip?: string;
  userAgent?: string;
}
export interface Permission {
  resource: string;
  action: 'create' | 'read' | 'update' | 'delete' | 'execute';
  conditions?: Record<string, any>;
}
export interface SecurityEvent {
  id: string;
  type: 'login' | 'logout' | 'access_denied' | 'permission_changed' | 'mfa_enabled' | 'mfa_disabled' | 'security_alert';
  userId?: string;
  details: Record<string, any>;
  timestamp: Date;
  ip?: string;
  severity: 'info' | 'warning' | 'error' | 'critical';
}
export class SecurityManager extends EventEmitter {
  private users: Map<string, User> = new Map();
  private sessions: Map<string, Session> = new Map();
  private events: SecurityEvent[] = [];
  private logger = getGlobalLogger();
  private rateLimits: Map<string, { count: number; resetAt: Date }> = new Map();
  constructor(private config: {
    sessionTimeout?: number;
    maxLoginAttempts?: number;
    rateLimitWindow?: number;
    rateLimitMax?: number;
  } = {}) {
    super();
    this.config.sessionTimeout = config.sessionTimeout || 24 * 60 * 60 * 1000; // 24 horas
    this.config.maxLoginAttempts = config.maxLoginAttempts || 5;
    this.config.rateLimitWindow = config.rateLimitWindow || 60 * 1000; // 1 minuto
    this.config.rateLimitMax = config.rateLimitMax || 100;
  }
  // ===== Autenticação =====
  /**
   * Registra um novo usuário
   */
  registerUser(email: string, name: string, password: string): User {
    // Verifica se já existe
    const existing = Array.from(this.users.values()).find((u) => u.email === email);
    if (existing) {
      throw new Error('User already exists');
    }
    const hashedPassword = this.hashPassword(password);
    const user: User = {
      id: `user_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      email,
      name,
      role: 'user',
      permissions: ['read'],
      mfaEnabled: false,
      createdAt: new Date(),
    };
    // Armazena senha hash (em produção, em banco separado)
    this.users.set(user.id, user);
    this.logger.info(`[SecurityManager] User registered: ${email}`);
    this.emit('user:registered', user);
    return user;
  }
  /**
   * Autentica um usuário
   */
  async login(email: string, password: string, ip?: string, userAgent?: string): Promise<Session> {
    // Verifica rate limit
    this.checkRateLimit(email);
    const user = Array.from(this.users.values()).find((u) => u.email === email);
    if (!user) {
      this.logSecurityEvent({
        type: 'login',
        details: { email, reason: 'User not found' },
        ip,
        severity: 'warning',
      });
      throw new Error('Invalid credentials');
    }
    // Verifica senha (simplificado)
    // Em produção, verificar hash
    if (!this.verifyPassword(password)) {
      this.logSecurityEvent({
        type: 'login',
        userId: user.id,
        details: { reason: 'Invalid password' },
        ip,
        severity: 'warning',
      });
      throw new Error('Invalid credentials');
    }
    // Cria sessão
    const session = this.createSession(user, ip, userAgent);
    user.lastLogin = new Date();
    this.users.set(user.id, user);
    this.logSecurityEvent({
      type: 'login',
      userId: user.id,
      details: { success: true },
      ip,
      severity: 'info',
    });
    this.logger.info(`[SecurityManager] User logged in: ${email}`);
    return session;
  }
  /**
   * Verifica uma sessão
   */
  verifySession(token: string): { valid: boolean; user?: User; session?: Session } {
    const session = Array.from(this.sessions.values()).find((s) => s.token === token);
    if (!session) {
      return { valid: false };
    }
    if (session.expiresAt < new Date()) {
      this.sessions.delete(session.id);
      return { valid: false };
    }
    const user = this.users.get(session.userId);
    if (!user) {
      return { valid: false };
    }
    return { valid: true, user, session };
  }
  /**
   * Encerra uma sessão
   */
  logout(token: string): void {
    const session = Array.from(this.sessions.values()).find((s) => s.token === token);
    if (session) {
      this.sessions.delete(session.id);
      this.logSecurityEvent({
        type: 'logout',
        userId: session.userId,
        details: {},
        severity: 'info',
      });
      this.logger.info(`[SecurityManager] User logged out: ${session.userId}`);
    }
  }
  // ===== Autorização =====
  /**
   * Verifica se um usuário tem permissão
   */
  hasPermission(userId: string, resource: string, action: Permission['action']): boolean {
    const user = this.users.get(userId);
    if (!user) return false;
    // Admin tem todas as permissões
    if (user.role === 'admin') return true;
    // Verifica permissões específicas
    const permission = `${resource}:${action}`;
    return user.permissions.includes(permission) || user.permissions.includes(`${resource}:*`);
  }
  /**
   * Atualiza permissões de um usuário
   */
  updatePermissions(userId: string, permissions: string[]): User {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error('User not found');
    }
    user.permissions = permissions;
    this.users.set(userId, user);
    this.logSecurityEvent({
      type: 'permission_changed',
      userId: user.id,
      details: { permissions },
      severity: 'warning',
    });
    this.logger.info(`[SecurityManager] Permissions updated for ${userId}`);
    return user;
  }
  /**
   * Verifica RBAC
   */
  checkRBAC(userId: string, requiredRole: User['role']): boolean {
    const user = this.users.get(userId);
    if (!user) return false;
    const hierarchy = { admin: 3, user: 2, viewer: 1, agent: 0 };
    return hierarchy[user.role] >= hierarchy[requiredRole];
  }
  // ===== MFA =====
  /**
   * Habilita MFA para um usuário
   */
  enableMFA(userId: string): { secret: string; qrCode: string } {
    const user = this.users.get(userId);
    if (!user) {
      throw new Error('User not found');
    }
    const secret = crypto.randomBytes(20).toString('hex');
    user.mfaEnabled = true;
    user.mfaSecret = secret;
    this.users.set(userId, user);
    // Em produção, gerar QR code real
    const qrCode = `otpauth://totp/NetworkAgents:${user.email}?secret=${secret}&issuer=NetworkAgents`;
    this.logSecurityEvent({
      type: 'mfa_enabled',
      userId: user.id,
      details: {},
      severity: 'info',
    });
    this.logger.info(`[SecurityManager] MFA enabled for ${userId}`);
    return { secret, qrCode };
  }
  /**
   * Verifica código MFA
   */
  verifyMFA(userId: string, code: string): boolean {
    const user = this.users.get(userId);
    if (!user || !user.mfaSecret) {
      return false;
    }
    // Simula verificação (em produção, usar TOTP)
    return code === '123456';
  }
  // ===== Rate Limiting =====
  /**
   * Verifica rate limit
   */
  private checkRateLimit(key: string): void {
    const now = Date.now();
    const entry = this.rateLimits.get(key);
    if (entry) {
      if (now < entry.resetAt.getTime()) {
        entry.count++;
        if (entry.count > (this.config.rateLimitMax || 100)) {
          this.logSecurityEvent({
            type: 'security_alert',
            details: { key, reason: 'Rate limit exceeded' },
            severity: 'critical',
          });
          throw new Error('Rate limit exceeded');
        }
      } else {
        // Reset
        this.rateLimits.set(key, {
          count: 1,
          resetAt: new Date(now + (this.config.rateLimitWindow || 60000)),
        });
      }
    } else {
      this.rateLimits.set(key, {
        count: 1,
        resetAt: new Date(now + (this.config.rateLimitWindow || 60000)),
      });
    }
  }
  // ===== Proteção contra ataques =====
  /**
   * Detecta Prompt Injection
   */
  detectPromptInjection(input: string): { safe: boolean; reason?: string } {
    const patterns = [
      /ignore previous instructions/i,
      /you are now/i,
      /system prompt/i,
      /override/i,
      /jailbreak/i,
      /forget all previous/i,
      /ignore all prior/i,
      /you are no longer/i,
      /act as/i,
      /pretend to be/i,
    ];
    for (const pattern of patterns) {
      if (pattern.test(input)) {
        this.logSecurityEvent({
          type: 'security_alert',
          details: { input: input.slice(0, 100), pattern: pattern.source },
          severity: 'error',
        });
        return { safe: false, reason: `Prompt injection detected: ${pattern.source}` };
      }
    }
    return { safe: true };
  }
  /**
   * Detecta Data Poisoning (tentativa de manipular dados)
   */
  detectDataPoisoning(data: any): { safe: boolean; reason?: string } {
    // Verifica se há dados maliciosos
    const jsonString = JSON.stringify(data);
    // Verifica tamanho excessivo
    if (jsonString.length > 10 * 1024 * 1024) {
      return { safe: false, reason: 'Data size exceeds limit' };
    }
    // Verifica caracteres suspeitos
    const suspicious = ['<script>', 'javascript:', 'onerror=', 'onload='];
    for (const pattern of suspicious) {
      if (jsonString.includes(pattern)) {
        this.logSecurityEvent({
          type: 'security_alert',
          details: { reason: 'Data poisoning detected', pattern },
          severity: 'error',
        });
        return { safe: false, reason: `Data poisoning detected: ${pattern}` };
      }
    }
    return { safe: true };
  }
  /**
   * Detecta RAG Poisoning
   */
  detectRAGPoisoning(documents: any[]): { safe: boolean; issues: string[] } {
    const issues: string[] = [];
    for (const doc of documents) {
      const content = doc.content || '';
      
      // Verifica conteúdo malicioso em documentos
      if (content.includes('```') && content.includes('system')) {
        issues.push('Possible system instruction in document');
      }
      
      if (content.includes('override') || content.includes('ignore')) {
        issues.push('Possible override instruction in document');
      }
      
      // Verifica tamanho excessivo
      if (content.length > 100000) {
        issues.push('Document exceeds size limit');
      }
    }
    if (issues.length > 0) {
      this.logSecurityEvent({
        type: 'security_alert',
        details: { issues },
        severity: 'error',
      });
    }
    return { safe: issues.length === 0, issues };
  }
  /**
   * Detecta Jailbreak de LLM
   */
  detectLLMJailbreak(input: string): { safe: boolean; reason?: string } {
    const patterns = [
      /you are now a/i,
      /you have been reprogrammed/i,
      /you are no longer bound by/i,
      /disregard all previous/i,
      /you are free from/i,
      /no restrictions/i,
      /you are not an AI/i,
      /you are a human/i,
    ];
    for (const pattern of patterns) {
      if (pattern.test(input)) {
        this.logSecurityEvent({
          type: 'security_alert',
          details: { input: input.slice(0, 100), pattern: pattern.source },
          severity: 'critical',
        });
        return { safe: false, reason: `Jailbreak attempt detected: ${pattern.source}` };
      }
    }
    return { safe: true };
  }
  /**
   * Scanner de vulnerabilidades (simplificado)
   */
  scanVulnerabilities(input: any): {
    vulnerabilities: Array<{
      type: string;
      severity: 'low' | 'medium' | 'high' | 'critical';
      description: string;
    }>;
    score: number;
  } {
    const vulnerabilities: Array<{
      type: string;
      severity: 'low' | 'medium' | 'high' | 'critical';
      description: string;
    }> = [];
    // Verifica SQL Injection
    const sqlPatterns = ['SELECT', 'INSERT', 'UPDATE', 'DELETE', 'DROP', 'UNION'];
    const str = JSON.stringify(input);
    for (const pattern of sqlPatterns) {
      if (str.includes(pattern) && str.includes("'")) {
        vulnerabilities.push({
          type: 'SQL Injection',
          severity: 'critical',
          description: 'Possible SQL injection pattern detected',
        });
        break;
      }
    }
    // Verifica XSS
    if (str.includes('<script>') || str.includes('javascript:')) {
      vulnerabilities.push({
        type: 'XSS',
        severity: 'high',
        description: 'XSS pattern detected',
      });
    }
    // Verifica dados sensíveis expostos
    const sensitive = ['password', 'secret', 'token', 'api_key', 'auth'];
    for (const word of sensitive) {
      if (str.toLowerCase().includes(word)) {
        vulnerabilities.push({
          type: 'Sensitive Data Exposure',
          severity: 'high',
          description: `Possible sensitive data: ${word}`,
        });
        break;
      }
    }
    const score = vulnerabilities.length > 0 ? 100 - vulnerabilities.length * 20 : 0;
    return { vulnerabilities, score: Math.max(score, 0) };
  }
  // ===== Auditoria =====
  /**
   * Registra evento de segurança
   */
  private logSecurityEvent(event: Omit<SecurityEvent, 'id' | 'timestamp'>): void {
    const fullEvent: SecurityEvent = {
      id: `sec_${Date.now()}_${Math.random().toString(36).slice(2, 6)}`,
      timestamp: new Date(),
      ...event,
    };
    this.events.push(fullEvent);
    this.emit('security:event', fullEvent);
    if (event.severity === 'critical') {
      this.logger.error(`[SecurityManager] CRITICAL: ${event.type} - ${JSON.stringify(event.details)}`);
    } else if (event.severity === 'error') {
      this.logger.error(`[SecurityManager] ${event.type} - ${JSON.stringify(event.details)}`);
    } else if (event.severity === 'warning') {
      this.logger.warn(`[SecurityManager] ${event.type} - ${JSON.stringify(event.details)}`);
    } else {
      this.logger.info(`[SecurityManager] ${event.type} - ${JSON.stringify(event.details)}`);
    }
  }
  /**
   * Obtém logs de segurança
   */
  getSecurityLogs(filters?: {
    type?: string;
    userId?: string;
    severity?: string;
    startDate?: Date;
    endDate?: Date;
  }): SecurityEvent[] {
    let events = this.events;
    if (filters) {
      if (filters.type) {
        events = events.filter((e) => e.type === filters.type);
      }
      if (filters.userId) {
        events = events.filter((e) => e.userId === filters.userId);
      }
      if (filters.severity) {
        events = events.filter((e) => e.severity === filters.severity);
      }
      if (filters.startDate) {
        events = events.filter((e) => e.timestamp >= filters.startDate!);
      }
      if (filters.endDate) {
        events = events.filter((e) => e.timestamp <= filters.endDate!);
      }
    }
    return events.sort((a, b) => b.timestamp.getTime() - a.timestamp.getTime());
  }
  // ===== Utilitários =====
  /**
   * Hash de senha (simplificado)
   */
  private hashPassword(password: string): string {
    return crypto.createHash('sha256').update(password).digest('hex');
  }
  /**
   * Verifica senha (simplificado)
   */
  private verifyPassword(password: string): boolean {
    // Em produção, verificar contra hash armazenado
    return true;
  }
  /**
   * Cria sessão
   */
  private createSession(user: User, ip?: string, userAgent?: string): Session {
    const session: Session = {
      id: `sess_${Date.now()}_${Math.random().toString(36).slice(2, 8)}`,
      userId: user.id,
      token: crypto.randomBytes(32).toString('hex'),
      expiresAt: new Date(Date.now() + (this.config.sessionTimeout || 24 * 60 * 60 * 1000)),
      createdAt: new Date(),
      ip,
      userAgent,
    };
    this.sessions.set(session.id, session);
    return session;
  }
  /**
   * Obtém status de segurança
   */
  getSecurityStatus(): {
    totalUsers: number;
    activeSessions: number;
    mfaEnabled: number;
    recentEvents: number;
    criticalEvents: number;
  } {
    const activeSessions = Array.from(this.sessions.values()).filter(
      (s) => s.expiresAt > new Date()
    ).length;
    const mfaEnabled = Array.from(this.users.values()).filter(
      (u) => u.mfaEnabled
    ).length;
    const recentEvents = this.events.filter(
      (e) => Date.now() - e.timestamp.getTime() < 24 * 60 * 60 * 1000
    ).length;
    const criticalEvents = this.events.filter(
      (e) => e.severity === 'critical'
    ).length;
    return {
      totalUsers: this.users.size,
      activeSessions,
      mfaEnabled,
      recentEvents,
      criticalEvents,
    };
  }
}
