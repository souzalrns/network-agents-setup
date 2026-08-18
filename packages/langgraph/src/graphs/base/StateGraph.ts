import { StateManager, GraphState } from '../../state/StateManager';
import { getGlobalLogger } from '@network-agents/observability';
export type GraphNode = (state: GraphState) => Promise<Partial<GraphState>>;
export type GraphEdge = (state: GraphState) => string | Promise<string>;
export class StateGraph {
  private nodes: Map<string, GraphNode> = new Map();
  private edges: Map<string, GraphEdge> = new Map();
  private entryPoint: string = '';
  private logger = getGlobalLogger();
  addNode(name: string, node: GraphNode): this {
    this.nodes.set(name, node);
    return this;
  }
  addEdge(from: string, to: string | GraphEdge): this {
    if (typeof to === 'string') {
      this.edges.set(from, () => to);
    } else {
      this.edges.set(from, to);
    }
    return this;
  }
  setEntryPoint(name: string): this {
    this.entryPoint = name;
    return this;
  }
  async run(initialState: Partial<GraphState>): Promise<GraphState> {
    const stateManager = new StateManager(initialState);
    let currentState = stateManager.getState();
    let currentNode = this.entryPoint;
    this.logger.info('Graph started', { entryPoint: currentNode });
    while (currentNode) {
      const nodeFn = this.nodes.get(currentNode);
      if (!nodeFn) {
        throw new Error(`Node ${currentNode} not found`);
      }
      this.logger.debug(`Executing node: ${currentNode}`, {
        status: currentState.status,
      });
      try {
        const updates = await nodeFn(currentState);
        stateManager.update(updates);
        currentState = stateManager.getState();
      } catch (error: any) {
        this.logger.error(`Node ${currentNode} failed`, { error: error.message });
        stateManager.addError(`Node ${currentNode}: ${error.message}`);
        stateManager.setStatus('failed');
        currentState = stateManager.getState();
        break;
      }
      const edgeFn = this.edges.get(currentNode);
      if (!edgeFn) {
        break;
      }
      const nextNode = await edgeFn(currentState);
      if (!nextNode || nextNode === currentNode) {
        break;
      }
      currentNode = nextNode;
    }
    stateManager.update({ endTime: new Date() });
    this.logger.info('Graph completed', {
      status: stateManager.getStatus(),
      duration: stateManager.getState().endTime
        ? stateManager.getState().endTime.getTime() - stateManager.getState().startTime.getTime()
        : 0,
    });
    return stateManager.getState();
  }
}
