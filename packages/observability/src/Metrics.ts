export interface MetricData {
  name: string;
  value: number;
  labels?: Record<string, string>;
  type: 'counter' | 'gauge' | 'histogram' | 'summary';
  description?: string;
}
export class Metrics {
  private counters: Map<string, number> = new Map();
  private gauges: Map<string, number> = new Map();
  private histograms: Map<string, number[]> = new Map();
  counter(name: string, labels?: Record<string, string>, value: number = 1): void {
    const key = this.buildKey(name, labels);
    this.counters.set(key, (this.counters.get(key) || 0) + value);
  }
  gauge(name: string, labels?: Record<string, string>, value: number = 0): void {
    const key = this.buildKey(name, labels);
    this.gauges.set(key, value);
  }
  histogram(name: string, labels?: Record<string, string>, value: number = 0): void {
    const key = this.buildKey(name, labels);
    const values = this.histograms.get(key) || [];
    values.push(value);
    this.histograms.set(key, values);
  }
  getMetrics(): MetricData[] {
    const metrics: MetricData[] = [];
    for (const [key, value] of this.counters) {
      const { name, labels } = this.parseKey(key);
      metrics.push({ name, value, labels, type: 'counter' });
    }
    for (const [key, value] of this.gauges) {
      const { name, labels } = this.parseKey(key);
      metrics.push({ name, value, labels, type: 'gauge' });
    }
    for (const [key, values] of this.histograms) {
      const { name, labels } = this.parseKey(key);
      if (values.length > 0) {
        const sum = values.reduce((a, b) => a + b, 0);
        metrics.push({ name: `${name}_avg`, value: sum / values.length, labels, type: 'summary' });
        metrics.push({ name: `${name}_count`, value: values.length, labels, type: 'counter' });
      }
    }
    return metrics;
  }
  private buildKey(name: string, labels?: Record<string, string>): string {
    if (!labels || Object.keys(labels).length === 0) return name;
    const labelStr = Object.entries(labels).sort().map(([k, v]) => `${k}=${v}`).join(',');
    return `${name}{${labelStr}}`;
  }
  private parseKey(key: string): { name: string; labels: Record<string, string> } {
    const match = key.match(/^([^{]+)\{([^}]+)\}$/);
    if (!match) return { name: key, labels: {} };
    const [, name, labelStr] = match;
    const labels: Record<string, string> = {};
    for (const pair of labelStr.split(',')) {
      const [k, v] = pair.split('=');
      labels[k] = v;
    }
    return { name, labels };
  }
  clear(): void {
    this.counters.clear();
    this.gauges.clear();
    this.histograms.clear();
  }
}
let globalMetrics: Metrics | null = null;
export function getGlobalMetrics(): Metrics {
  if (!globalMetrics) globalMetrics = new Metrics();
  return globalMetrics;
}
