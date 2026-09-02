import React, { createContext, useContext, useEffect, useState, useRef } from 'react';
import { getWsUrl } from '../config/api';

export type TrainStatus = 'ON_TIME' | 'DELAYED' | 'CRITICAL';

export interface HistoricalContext {
  month: string;
  season: string;
  region: string;
  departure_time: string;
  departure_hour: number;
  historical_fog_risk: number;
  historical_fog_risk_pct: number;
  historical_congestion_risk: number;
  historical_congestion_risk_pct: number;
  mean_delay_fog_min: number;
  sample_count: number;
  reliability: string;
}

export interface System2Prediction {
  fogRiskPct: number;
  congestionRiskPct: number;
  operationalRiskPct: number;
  confidencePct: number;
  expectedSpeedImpact: string;
}

export interface System3Decision {
  restrictionActive: boolean;
  actionType: string;
  speedCapKmph: number | null;
  reason: string;
}

export interface CycleInfo {
  lastUpdated: string;
  nextPrediction: string;
  cycleSec: number;
}

export interface Train {
  id: string;
  name: string;
  route: string;
  currentLocation: string;
  currentSpeed?: number;
  simTime?: string;
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
  historicalContext?: HistoricalContext;
  system2Prediction?: System2Prediction;
  system3Decision?: System3Decision;
  cycleInfo?: CycleInfo;
}

interface WebSocketContextType {
  liveTrains: Train[];
  isConnected: boolean;
  selectedMonth: string;
  setMonth: (month: string) => void;
}

const WebSocketContext = createContext<WebSocketContextType>({
  liveTrains: [],
  isConnected: false,
  selectedMonth: 'February',
  setMonth: () => {},
});

export const WebSocketProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [liveTrains, setLiveTrains] = useState<Train[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [selectedMonth, setSelectedMonthState] = useState<string>('February');
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let ws: WebSocket;
    let isMounted = true;

    const connect = () => {
      const wsUrl = getWsUrl('/ws/live');
      ws = new WebSocket(wsUrl);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isMounted) {
          console.log('Connected to Live Train WebSocket');
          setIsConnected(true);
        }
      };

      ws.onmessage = (event) => {
        try {
          const payload = JSON.parse(event.data);
          if (payload.type === 'LIVE_TRAINS' && isMounted) {
            setLiveTrains(payload.data || []);
            if (payload.selected_month) {
              setSelectedMonthState(payload.selected_month);
            }
          }
        } catch (err) {
          console.error('Error parsing WS message', err);
        }
      };

      ws.onclose = () => {
        if (isMounted) {
          console.log('Disconnected from Live Train WebSocket, retrying in 3s...');
          setIsConnected(false);
          setTimeout(connect, 3000);
        }
      };

      ws.onerror = (err) => {
        console.error('WebSocket Error', err);
        ws.close();
      };
    };

    connect();

    return () => {
      isMounted = false;
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, []);

  const setMonth = (month: string) => {
    setSelectedMonthState(month);
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({ type: 'SET_MONTH', month }));
    }
  };

  return (
    <WebSocketContext.Provider value={{ liveTrains, isConnected, selectedMonth, setMonth }}>
      {children}
    </WebSocketContext.Provider>
  );
};

export const useWebSocket = () => useContext(WebSocketContext);
