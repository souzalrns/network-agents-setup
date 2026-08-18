// Dashboard simples para visualizar métricas
export function Dashboard() {
  const [metrics, setMetrics] = useState<any>(null);
  useEffect(() => {
    fetch('/metrics')
      .then((res) => res.json())
      .then(setMetrics);
  }, []);
  if (!metrics) return <div>Loading...</div>;
  return (
    <div>
      <h1>Network Agents Dashboard</h1>
      
      <div className="grid grid-cols-4 gap-4">
        <MetricCard title="Total Execuções" value={metrics.total} />
        <MetricCard title="Sucesso" value={metrics.successful} />
        <MetricCard title="Falhas" value={metrics.failed} />
        <MetricCard title="Taxa de Sucesso" value={metrics.successRate} />
        <MetricCard title="Total Tokens" value={metrics.totalTokens.toLocaleString()} />
        <MetricCard title="Custo Total" value={`€${metrics.totalCost.toFixed(2)}`} />
        <MetricCard title="Tempo Médio" value={`${metrics.averageDurationMs.toFixed(0)}ms`} />
        <MetricCard title="Agentes" value={Object.keys(metrics.byAgent).length} />
      </div>
      <div className="mt-8">
        <h2>Execuções por Agente</h2>
        <BarChart data={metrics.byAgent} />
      </div>
      <div className="mt-8">
        <h2>Execuções por Domínio</h2>
        <PieChart data={metrics.byDomain} />
      </div>
      <div className="mt-8">
        <h2>Série Temporal</h2>
        <LineChart data={metrics.timeSeries} />
      </div>
    </div>
  );
}
