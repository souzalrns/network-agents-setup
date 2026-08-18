import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';
import { ImmunologicalMemory } from '../immunity/ImmunologicalMemory';

export interface WorkerStatus {
  id: string;
  type: string;
  status: 'running' | 'stopped' | 'error' | 'degraded';
  lastHeartbeat: Date;
  uptime: number; // segundos
  tasksCompleted: number;
  tasksFailed: number;
  memoryUsage: number; // MB
  cpuUsage: number; // %
  metadata: Record<string, any>;
}

export interface WorkerHeartbeat {
  workerId: string;
  timestamp: Date;
  status: 'running' | 'degraded' | 'error';
  tasks: number;
  memoryUsage: number;
  cpuUsage: number;
  metadata: Record<string, any>;
}

export class WorkerSupervisor extends EventEmitter {
  private logger = getGlobalLogger();
  private workers: Map<string, WorkerStatus> = new Map();
  private heartbeats: Map<string, WorkerHeartbeat[]> = new Map();
  private checkInterval: NodeJS.Timeout | null = null;

  constructor(
    private immunologicalMemory: ImmunologicalMemory,
    private config: {
      heartbeatTimeout?: number; // ms
      checkInterval?: number; // ms
      maxRestartAttempts?: number;
    } = {}
  ) {
    super();
    this.config.heartbeatTimeout = config.heartbeatTimeout || 30000; // 30 segundos
    this.config.checkInterval = config.checkInterval || 10000; // 10 segundos
    this.config.maxRestartAttempts = config.maxRestartAttempts || 3;

    // Inicia verificação periódica
    this.checkInterval = setInterval(() => this.checkWorkers(), this.config.checkInterval);
    this.logger.info('[WorkerSupervisor] Initialized');
  }

  /**
   * Registra um worker
   */
  registerWorker(workerId: string, type: string, metadata: Record<string, any> = {}): void {
    const status: WorkerStatus = {
      id: workerId,
      type,
      status: 'running',
      lastHeartbeat: new Date(),
      uptime: 0,
      tasksCompleted: 0,
      tasksFailed: 0,
      memoryUsage: 0,
      cpuUsage: 0,
      metadata,
    };

    this.workers.set(workerId, status);
    this.heartbeats.set(workerId, []);

    this.logger.info(`[WorkerSupervisor] Worker registered: ${workerId} (${type})`);
    this.emit('worker:registered', status);
  }

  /**
   * Recebe heartbeat de um worker
   */
  receiveHeartbeat(heartbeat: WorkerHeartbeat): void {
    const status = this.workers.get(heartbeat.workerId);
    if (!status) {
      this.logger.warn(`[WorkerSupervisor] Heartbeat from unknown worker: ${heartbeat.workerId}`);
      return;
    }

    // Atualiza status
    // Bug corrigido: o delta de uptime precisa ser calculado a partir do
    // lastHeartbeat ANTERIOR, antes de sobrescrevê-lo com o valor atual.
    const previousHeartbeat = status.lastHeartbeat;
    status.lastHeartbeat = new Date();
    status.status = heartbeat.status;
    status.memoryUsage = heartbeat.memoryUsage;
    status.cpuUsage = heartbeat.cpuUsage;
    status.uptime += (status.lastHeartbeat.getTime() - previousHeartbeat.getTime()) / 1000;

    // Atualiza contagem de tarefas
    if (heartbeat.tasks !== undefined) {
      // Diferença desde o último heartbeat
      const lastHeartbeat = this.heartbeats.get(heartbeat.workerId)?.slice(-1)[0];
      if (lastHeartbeat && heartbeat.tasks > lastHeartbeat.tasks) {
        status.tasksCompleted += heartbeat.tasks - lastHeartbeat.tasks;
      }
    }

    this.workers.set(heartbeat.workerId, status);

    // Armazena heartbeat
    const heartbeats = this.heartbeats.get(heartbeat.workerId) || [];
    heartbeats.push(heartbeat);
    if (heartbeats.length > 100) {
      heartbeats.shift(); // Mantém apenas os 100 mais recentes
    }
    this.heartbeats.set(heartbeat.workerId, heartbeats);

    this.emit('worker:heartbeat', heartbeat);
  }

  /**
   * Verifica todos os workers
   */
  private checkWorkers(): void {
    const now = new Date();

    for (const [workerId, status] of this.workers) {
      const timeSinceHeartbeat = now.getTime() - status.lastHeartbeat.getTime();

      if (timeSinceHeartbeat > (this.config.heartbeatTimeout || 30000)) {
        // Worker não respondeu
        this.logger.warn(`[WorkerSupervisor] Worker ${workerId} missed heartbeat (${timeSinceHeartbeat}ms)`);

        if (status.status !== 'error') {
          status.status = 'degraded';
          this.workers.set(workerId, status);

          // Registra na memória imunológica
          this.immunologicalMemory.registerEvent({
            type: 'incident',
            severity: 'high',
            description: `Worker ${workerId} missed heartbeat`,
            rootCause: 'heartbeat_timeout',
            impact: {
              components: [workerId],
              durationMs: timeSinceHeartbeat,
              dataLoss: false,
              serviceDegradation: true,
            },
            response: {
              action: 'checking',
              executedBy: 'WorkerSupervisor',
              durationMs: 0,
              success: false,
            },
            learnings: ['Worker pode estar sobrecarregado ou travado'],
            recommendations: ['Reiniciar worker ou aumentar timeout'],
            status: 'open',
            metadata: { workerId, timeSinceHeartbeat },
          });

          this.emit('worker:missed_heartbeat', { workerId, status, timeSinceHeartbeat });

          // Tenta recuperar automaticamente
          this.attemptRecovery(workerId);
        }
      }
    }
  }

  /**
   * Tenta recuperar um worker
   */
  private async attemptRecovery(workerId: string): Promise<void> {
    const status = this.workers.get(workerId);
    if (!status) return;

    const attempts = (status.metadata?.recoveryAttempts || 0) + 1;
    status.metadata = { ...status.metadata, recoveryAttempts: attempts };

    if (attempts <= (this.config.maxRestartAttempts || 3)) {
      this.logger.info(`[WorkerSupervisor] Attempting recovery for ${workerId} (attempt ${attempts})`);

      // Simula reinicialização
      status.status = 'running';
      status.lastHeartbeat = new Date();
      this.workers.set(workerId, status);

      this.emit('worker:recovery_attempted', { workerId, attempts });

      this.immunologicalMemory.registerEvent({
        type: 'recovery',
        severity: 'medium',
        description: `Worker ${workerId} recovery attempted (${attempts})`,
        rootCause: 'manual_recovery',
        impact: {
          components: [workerId],
          durationMs: 0,
          dataLoss: false,
          serviceDegradation: false,
        },
        response: {
          action: 'recovery_attempt',
          executedBy: 'WorkerSupervisor',
          durationMs: 0,
          success: true,
        },
        learnings: ['Recuperação automática iniciada'],
        recommendations: ['Monitorar worker após recuperação'],
        status: 'resolved',
        metadata: { workerId, attempts },
      });
    } else {
      // Máximo de tentativas atingido
      status.status = 'error';
      this.workers.set(workerId, status);

      this.logger.error(`[WorkerSupervisor] Worker ${workerId} failed after ${attempts} recovery attempts`);

      this.immunologicalMemory.registerEvent({
        type: 'failure',
        severity: 'critical',
        description: `Worker ${workerId} failed after ${attempts} recovery attempts`,
        rootCause: 'max_recovery_attempts',
        impact: {
          components: [workerId],
          durationMs: 0,
          dataLoss: false,
          serviceDegradation: true,
        },
        response: {
          action: 'escalated',
          executedBy: 'WorkerSupervisor',
          durationMs: 0,
          success: false,
        },
        learnings: ['Worker precisa de intervenção manual'],
        recommendations: ['Verificar logs e reiniciar manualmente'],
        status: 'open',
        metadata: { workerId, attempts },
      });

      this.emit('worker:failed', { workerId, status, attempts });
    }
  }

  /**
   * Obtém status de um worker
   */
  getWorkerStatus(workerId: string): WorkerStatus | undefined {
    return this.workers.get(workerId);
  }

  /**
   * Obtém status de todos os workers
   */
  getAllWorkers(): WorkerStatus[] {
    return Array.from(this.workers.values());
  }

  /**
   * Obtém heartbeats de um worker
   */
  getHeartbeats(workerId: string): WorkerHeartbeat[] {
    return this.heartbeats.get(workerId) || [];
  }

  /**
   * Obtém estatísticas
   */
  getStats(): {
    totalWorkers: number;
    running: number;
    stopped: number;
    error: number;
    degraded: number;
  } {
    const workers = Array.from(this.workers.values());
    return {
      totalWorkers: workers.length,
      running: workers.filter((w) => w.status === 'running').length,
      stopped: workers.filter((w) => w.status === 'stopped').length,
      error: workers.filter((w) => w.status === 'error').length,
      degraded: workers.filter((w) => w.status === 'degraded').length,
    };
  }

  /**
   * Para o supervisor
   */
  stop(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = null;
    }
    this.logger.info('[WorkerSupervisor] Stopped');
  }
}
