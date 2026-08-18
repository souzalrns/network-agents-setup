export interface LogEntry {
  timestamp: Date;
  level: 'debug' | 'info' | 'warn' | 'error';
  message: string;
  component: string;
  executionId?: string;
  agentId?: string;
  domain?: string;
  metadata?: Record<string, any>;
  error?: {
    message: string;
    stack?: string;
    code?: string;
  };
}
export interface MetricData {
  name: string;
  value: number;
  labels?: Record<string, string>;
  type: 'counter' | 'gauge' | 'histogram' | 'summary';
  description?: string;
}
export interface Span {
  id: string;
  traceId: string;
  parentId?: string;
  name: string;
  startTime: Date;
  endTime?: Date;
  durationMs?: number;
  status: 'ok' | 'error';
  attributes: Record<string, any>;
  events: Array<{
    name: string;
    timestamp: Date;
    attributes: Record<string, any>;
  }>;
}
export interface ObservabilityConfig {
  logLevel: 'debug' | 'info' | 'warn' | 'error';
  enableMetrics: boolean;
  enableTracing: boolean;
  metricsPort?: number;
  otlpEndpoint?: string;
  serviceName: string;
  environment: string;
}
