import { WebSocketRoom, WebSocketConnection } from '../types/websocket';
export class RoomManager {
  private rooms: Map<string, WebSocketRoom> = new Map();
  private connections: Map<string, WebSocketConnection> = new Map();
  addConnection(connectionId: string, metadata: Record<string, any> = {}): WebSocketConnection {
    const connection: WebSocketConnection = {
      id: connectionId,
      rooms: new Set(),
      isAuthenticated: false,
      connectedAt: new Date(),
      lastActivity: new Date(),
      metadata,
    };
    this.connections.set(connectionId, connection);
    return connection;
  }
  removeConnection(connectionId: string): void {
    const connection = this.connections.get(connectionId);
    if (!connection) return;
    for (const roomId of connection.rooms) {
      this.leaveRoom(connectionId, roomId);
    }
    this.connections.delete(connectionId);
  }
  getConnection(connectionId: string): WebSocketConnection | undefined {
    return this.connections.get(connectionId);
  }
  authenticateConnection(connectionId: string, userId: string): void {
    const connection = this.connections.get(connectionId);
    if (!connection) return;
    connection.userId = userId;
    connection.isAuthenticated = true;
  }
  updateConnectionActivity(connectionId: string): void {
    const connection = this.connections.get(connectionId);
    if (!connection) return;
    connection.lastActivity = new Date();
  }
  createRoom(roomId: string, name: string, metadata: Record<string, any> = {}): WebSocketRoom {
    const room: WebSocketRoom = {
      id: roomId,
      name,
      connections: new Set(),
      metadata,
    };
    this.rooms.set(roomId, room);
    return room;
  }
  removeRoom(roomId: string): void {
    const room = this.rooms.get(roomId);
    if (!room) return;
    for (const connectionId of room.connections) {
      const connection = this.connections.get(connectionId);
      if (connection) {
        connection.rooms.delete(roomId);
      }
    }
    this.rooms.delete(roomId);
  }
  joinRoom(connectionId: string, roomId: string): void {
    const connection = this.connections.get(connectionId);
    const room = this.rooms.get(roomId);
    if (!connection || !room) return;
    connection.rooms.add(roomId);
    room.connections.add(connectionId);
  }
  leaveRoom(connectionId: string, roomId: string): void {
    const connection = this.connections.get(connectionId);
    const room = this.rooms.get(roomId);
    if (!connection || !room) return;
    connection.rooms.delete(roomId);
    room.connections.delete(connectionId);
    if (room.connections.size === 0) {
      this.rooms.delete(roomId);
    }
  }
  getRoomConnections(roomId: string): string[] {
    const room = this.rooms.get(roomId);
    if (!room) return [];
    return Array.from(room.connections);
  }
  getConnectionRooms(connectionId: string): string[] {
    const connection = this.connections.get(connectionId);
    if (!connection) return [];
    return Array.from(connection.rooms);
  }
  getActiveConnections(): number {
    return this.connections.size;
  }
  getActiveRooms(): number {
    return this.rooms.size;
  }
  getConnectionStats(): {
    total: number;
    authenticated: number;
    byRoom: Record<string, number>;
  } {
    const stats = { total: this.connections.size, authenticated: 0, byRoom: {} as Record<string, number> };
    for (const [, connection] of this.connections) {
      if (connection.isAuthenticated) stats.authenticated++;
      for (const roomId of connection.rooms) {
        stats.byRoom[roomId] = (stats.byRoom[roomId] || 0) + 1;
      }
    }
    return stats;
  }
}
