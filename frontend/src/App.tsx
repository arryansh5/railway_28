
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import { Layout } from './components/Layout';
import { Dashboard } from './pages/Dashboard';
import { LiveTrains } from './pages/LiveTrains';
import { TrainDetails } from './pages/TrainDetails';
import { AiExplanations } from './pages/AiExplanations';
import { AlertsAccuracy } from './pages/AlertsAccuracy';

function App() {
  return (
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
  );
}

export default App;
