
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { LiveTrains } from './pages/LiveTrains';
import { TrainDetails } from './pages/TrainDetails';
import { AiExplanations } from './pages/AiExplanations';
import { AlertsAccuracy } from './pages/AlertsAccuracy';

import { WebSocketProvider } from './context/WebSocketContext';

function App() {
  return (
    <WebSocketProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Dashboard />} />
            <Route path="trains" element={<LiveTrains />} />
            <Route path="details" element={<TrainDetails />} />
            <Route path="predictions" element={<AiExplanations />} />
            <Route path="alerts" element={<AlertsAccuracy />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </WebSocketProvider>
  );
}

export default App;
