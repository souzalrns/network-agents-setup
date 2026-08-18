export interface LogEntry {
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  component: string;
  executionId?: string;
  agentId?: string;
  domain?: string;
  metadata?: Record<string, any>;
  error?: { message: string; stack?: string; code?: string };
}
export class Logger {
  private level: string;
  private component: string;
  private executionId?: string;
  constructor(component: string, level: string = 'info') {
    this.component = component;
    this.level = level;
  }
  setExecutionId(executionId: string): void {
    this.executionId = executionId;
  }
  debug(message: string, metadata?: Record<string, any>): void {
    this.log('debug', message, metadata);
  }
  info(message: string, metadata?: Record<string, any>): void {
    this.log('info', message, metadata);
  }
  warn(message: string, metadata?: Record<string, any>): void {
    this.log('warn', message, metadata);
  }
  error(message: string, metadata?: Record<string, any>): void {
    this.log('error', message, metadata);
  }
  errorWithStack(message: string, error: Error, metadata?: Record<string, any>): void {
    this.log('error', message, { ...metadata, error: { message: error.message, stack: error.stack } });
  }
  private log(level: string, message: string, metadata?: Record<string, any>): void {
    if (!this.shouldLog(level)) return;
    const entry: LogEntry = { timestamp: new Date(), level: level as any, message, component: this.component, executionId: this.executionId, metadata };
    console.log(JSON.stringify(entry));
  }
  private shouldLog(level: string): boolean {
    const levels = ['debug', 'info', 'warn', 'error'];
    return levels.indexOf(level) >= levels.indexOf(this.level);
  }
  child(component: string): Logger {
    const child = new Logger(component, this.level);
    child.setExecutionId(this.executionId);
    return child;
  }
}
let globalLogger: Logger | null = null;
export function getGlobalLogger(): Logger {
  if (!globalLogger) globalLogger = new Logger('app', process.env.LOG_LEVEL || 'info');
  return globalLogger;
}
export function createLogger(component: string): Logger {
  return new Logger(component, process.env.LOG_LEVEL || 'info');
}
