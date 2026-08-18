// Tipos para Simulation
export interface SimulationScenario {
  id: string;
  name: string;
  description: string;
  type: 'architectural' | 'economic' | 'operational' | 'evolutionary' | 'constitutional';
  parameters: Record<string, any>;
  initialState: any;
  duration: number;
  steps: number;
  status: 'draft' | 'running' | 'completed' | 'failed';
  createdAt: Date;
  completedAt?: Date;
  results?: SimulationResult;
}
export interface SimulationResult {
  success: boolean;
  metrics: {
    finalState: any;
    delta: Record<string, number>;
    roi: number;
    risk: number;
    stability: number;
  };
  events: SimulationEvent[];
  recommendations: string[];
  warnings: string[];
}
export interface SimulationEvent {
  id: string;
  timestamp: Date;
  type: 'change' | 'alert' | 'decision' | 'error';
  description: string;
  impact: number;
  affectedComponents: string[];
}
