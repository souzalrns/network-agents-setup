export interface GraphState {
  input: string;
  domain?: string;
  userId?: string;
  conversationId?: string;
  intent?: string;
  plan?: any;
  currentStep?: number;
  executionId?: string;
  results: Map<string, any>;
  errors: string[];
  status: 'idle' | 'planning' | 'executing' | 'validating' | 'completed' | 'failed';
  context: Record<string, any>;
  memory: any;
  hitlRequests: any[];
  pendingApproval?: any;
  metadata: Record<string, any>;
  startTime: Date;
  endTime?: Date;
  duration?: number;
}
export class StateManager {
  private state: GraphState;
  constructor(initialState: Partial<GraphState> = {}) {
    this.state = {
      input: '',
      results: new Map(),
      errors: [],
      status: 'idle',
      context: {},
      metadata: {},
      hitlRequests: [],
      startTime: new Date(),
      ...initialState,
    };
  }
  getState(): GraphState {
    return this.state;
  }
  update(updates: Partial<GraphState>): void {
    this.state = { ...this.state, ...updates };
  }
  setResult(key: string, value: any): void {
    this.state.results.set(key, value);
  }
  getResult(key: string): any {
    return this.state.results.get(key);
  }
  addError(error: string): void {
    this.state.errors.push(error);
  }
  hasErrors(): boolean {
    return this.state.errors.length > 0;
  }
  setStatus(status: GraphState['status']): void {
    this.state.status = status;
  }
  getStatus(): GraphState['status'] {
    return this.state.status;
  }
  snapshot(): GraphState {
    return {
      ...this.state,
      results: new Map(this.state.results),
      errors: [...this.state.errors],
      context: { ...this.state.context },
      metadata: { ...this.state.metadata },
      hitlRequests: [...this.state.hitlRequests],
    };
  }
  restore(snapshot: GraphState): void {
    this.state = {
      ...snapshot,
      results: new Map(snapshot.results),
      errors: [...snapshot.errors],
      context: { ...snapshot.context },
      metadata: { ...snapshot.metadata },
      hitlRequests: [...snapshot.hitlRequests],
    };
  }
}
