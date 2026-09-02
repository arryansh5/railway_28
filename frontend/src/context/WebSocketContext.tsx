import React, { createContext, useContext, useEffect, useState } from 'react';

// Re-export Train interface so we have it centralized
export type TrainStatus = 'ON_TIME' | 'DELAYED' | 'CRITICAL';

export interface Train {
  id: string;
  name: string;
  route: string;
  currentLocation: string;
  distanceRemaining: number;
  scheduledEta: string;
  aiEta: string;
  delayMin: number;
  confidence: number;
  status: TrainStatus;
  delayReason?: string;
  timeline?: {
    stationCode: string;
    stationName: string;
    scheduled: string;
    predicted: string;
    delay: number;
  }[];
}

interface WebSocketContextType {
  liveTrains: Train[];
  isConnected: boolean;
}

const WebSocketContext = createContext<WebSocketContextType>({
  liveTrains: [],
  isConnected: false,
});

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [liveTrains, setLiveTrains] = useState<Train[]>([]);
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    // Connect to FastAPI WebSocket
    const ws = new WebSocket('ws://localhost:8000/ws/live');

    ws.onopen = () => {
      console.log('Connected to Live Train WebSocket');
      setIsConnected(true);
    };

    ws.onmessage = (event) => {
      try {
        const payload = JSON.parse(event.data);
        if (payload.type === 'LIVE_TRAINS') {
          // Update the train states continuously like a chat app!
          setLiveTrains(payload.data);
        }
      } catch (err) {
        console.error('Error parsing WS message', err);
      }
    };

    ws.onclose = () => {
      console.log('Disconnected from Live Train WebSocket');
      setIsConnected(false);
    };

    return () => {
      ws.close();
    };
  }, []);

  return (
    <WebSocketContext.Provider value={{ liveTrains, isConnected }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
