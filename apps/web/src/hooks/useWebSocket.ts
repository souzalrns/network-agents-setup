import { useEffect, useState, useRef } from 'react';
import { WebSocketClient } from '@websocket/WebSocketClient';
export function useWebSocket(url: string) {
  const [isConnected, setIsConnected] = useState(false);
  const [messages, setMessages] = useState<any[]>([]);
  const clientRef = useRef<WebSocketClient | null>(null);
  useEffect(() => {
    const client = new WebSocketClient(url);
    clientRef.current = client;
    client.connect()
      .then(() => {
        setIsConnected(true);
        console.log('WebSocket connected');
      })
      .catch((error) => {
        console.error('WebSocket connection error:', error);
      });
    client.on('message', (message) => {
      setMessages((prev) => [...prev, message]);
    });
    client.on('event:execution:step:start', (data) => {
      console.log('Step started:', data);
    });
    client.on('event:execution:step:complete', (data) => {
      console.log('Step completed:', data);
    });
    client.on('event:execution:complete', (data) => {
      console.log('Execution complete:', data);
    });
    client.on('event:chat:stream:chunk', (data) => {
      console.log('Stream chunk:', data);
    });
    client.on('event:hitl:request', (data) => {
      console.log('HITL request:', data);
      // Mostrar notificação para o usuário
    });
    return () => {
      client.disconnect();
    };
  }, [url]);
  const send = (action: string, payload: any) => {
    if (clientRef.current) {
      clientRef.current.send(action, payload);
    } else {
      console.warn('WebSocket client not connected yet; message dropped', { action, payload });
    }
  };
  return {
    isConnected,
    messages,
    send,
    client: clientRef.current,
  };
}
