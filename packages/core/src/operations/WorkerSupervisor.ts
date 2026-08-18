import { EventEmitter } from 'events';
import { getGlobalLogger } from '@network-agents/observability';

// P-027: Supervisão de workers — monitoramento de heartbeat, detecção de
// heartbeats perdidos, recuperação automática com limite de tentativas
// e estatísticas de status dos workers.

export interface WorkerInfo {
  id: string;
  name: string;
  status: 'healthy' | 'degraded' | 'missed_heartbeat' | 'recovering' | 'failed';
  lastHeartbeat: Date;
  registeredAt: Date;
  recoveryAttempts: number;
  metadata?: Record<string, any>;
}

export class WorkerSupervisor extends EventEmitter {
  private workers: Map<string, WorkerInfo> = new Map();
  private logger = getGlobalLogger();
  private checkInterval?: NodeJS.Timeout;

  constructor(
    private config: {
      heartbeatTimeoutMs?: number;
      checkIntervalMs?: number;
      maxRecoveryAttempts?: number;
    } = {}
  ) {
    super();
    this.config.heartbeatTimeoutMs = config.heartbeatTimeoutMs ?? 30_000;
    this.config.checkIntervalMs = config.checkIntervalMs ?? 15_000;
    this.config.maxRecoveryAttempts = config.maxRecoveryAttempts ?? 3;

    if (this.config.checkIntervalMs > 0) {
      this.checkInterval = setInterval(() => this.checkMissedHeartbeats(), this.config.checkIntervalMs);
    }
  }

  registerWorker(id: string, name: string, metadata?: Record<string, any>): WorkerInfo {
    const worker: WorkerInfo = {
      id,
      name,
      status: 'healthy',
      lastHeartbeat: new Date(),
      registeredAt: new Date(),
      recoveryAttempts: 0,
      metadata,
    };
    this.workers.set(id, worker);
    this.logger.info(`[WorkerSupervisor] Worker registrado: ${id} (${name})`);
    this.emit('worker:registered', worker);
    return worker;
  }

  heartbeat(id: string): void {
    const worker = this.workers.get(id);
    if (!worker) return;
    worker.lastHeartbeat = new Date();
    if (worker.status !== 'healthy') {
      worker.status = 'healthy';
      worker.recoveryAttempts = 0;
      this.emit('worker:recovered', worker);
    }
    this.workers.set(id, worker);
  }

  checkMissedHeartbeats(): WorkerInfo[] {
    const now = Date.now();
    const timeout = this.config.heartbeatTimeoutMs || 30_000;
    const missed: WorkerInfo[] = [];

    for (const worker of this.workers.values()) {
      if (worker.status === 'failed') continue;
      const elapsed = now - worker.lastHeartbeat.getTime();
      if (elapsed > timeout) {
        worker.status = 'missed_heartbeat';
        missed.push(worker);
        this.logger.warn(`[WorkerSupervisor] Heartbeat perdido: ${worker.id} (${elapsed}ms)`);
        this.emit('worker:missed-heartbeat', worker);
        this.autoRecover(worker);
      }
    }
    return missed;
  }

  private autoRecover(worker: WorkerInfo): void {
    const max = this.config.maxRecoveryAttempts || 3;
    if (worker.recoveryAttempts >= max) {
      worker.status = 'failed';
      this.logger.error(`[WorkerSupervisor] Worker ${worker.id} falhou após ${worker.recoveryAttempts} tentativas de recuperação`);
      this.emit('worker:failed', worker);
      return;
    }
    worker.status = 'recovering';
    worker.recoveryAttempts += 1;
    this.logger.info(`[WorkerSupervisor] Tentando recuperar worker ${worker.id} (tentativa ${worker.recoveryAttempts}/${max})`);
    this.emit('worker:recovering', worker);
  }

  getWorker(id: string): WorkerInfo | undefined {
    return this.workers.get(id);
  }

  getAllWorkers(): WorkerInfo[] {
    return Array.from(this.workers.values());
  }

  getStats(): {
    total: number;
    healthy: number;
    degraded: number;
    failed: number;
  } {
    const all = this.getAllWorkers();
    return {
      total: all.length,
      healthy: all.filter((w) => w.status === 'healthy').length,
      degraded: all.filter((w) => w.status === 'missed_heartbeat' || w.status === 'recovering').length,
      failed: all.filter((w) => w.status === 'failed').length,
    };
  }

  stop(): void {
    if (this.checkInterval) {
      clearInterval(this.checkInterval);
      this.checkInterval = undefined;
    }
  }
}
