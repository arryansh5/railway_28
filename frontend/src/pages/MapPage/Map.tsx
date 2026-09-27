import React, { useMemo, useRef, useState, useCallback, useEffect } from 'react';
import Map, { Source, Layer, Marker } from 'react-map-gl/maplibre';
// @ts-ignore
import type { MapRef } from 'react-map-gl';
import * as maplibregl from 'maplibre-gl';
import 'maplibre-gl/dist/maplibre-gl.css';
import { Navigation2, Plus, Minus, Search, Menu, X, ArrowUpDown, Train, MapPin, Clock, ArrowLeft, ChevronDown, ChevronUp, ChevronLeft, ChevronRight, MapPin as MapPinIcon, Target, AlertTriangle, Activity, Info, CheckCircle2, Radio } from 'lucide-react';
import { buildGraph, findPaths } from '../../utils/router';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { useWebSocket } from '../../context/WebSocketContext';

const mapStyle = {
  version: 8,
  sources: {
    'esri-satellite': {
      type: 'raster',
      tiles: [
        'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
      ],
      tileSize: 256,
    },
    'esri-labels': {
      type: 'raster',
      tiles: [
        'https://services.arcgisonline.com/ArcGIS/rest/services/Reference/World_Boundaries_and_Places/MapServer/tile/{z}/{y}/{x}'
      ],
      tileSize: 256,
    }
  },
  layers: [
    {
      id: 'esri-satellite-layer',
      type: 'raster',
      source: 'esri-satellite',
      minzoom: 0,
      maxzoom: 22,
    },
    {
      id: 'esri-labels-layer',
      type: 'raster',
      source: 'esri-labels',
      minzoom: 0,
      maxzoom: 22,
    }
  ],
};

const normalizeStationName = (name: string) => {
  if (!name) return '';
  return name
    .toLowerCase()
    .replace(/ (jn|junction|juncion|cantt|cant|city|terminal|term|road)$/i, '')
    .replace(/[^a-z0-9]/g, '');
};

export const MapView: React.FC = () => {
  const mapRef = useRef<MapRef>(null);
  const [searchParams, setSearchParams] = useSearchParams();
  const navigate = useNavigate();
  const { liveTrains } = useWebSocket();

  const [hoverInfo, setHoverInfo] = useState<{ feature: any, x: number, y: number } | null>(null);
  const [selectedStationId, setSelectedStationId] = useState<string | null>(null);
  const [showDensityHeatmap, setShowDensityHeatmap] = useState(false);

  const [stationsMeta, setStationsMeta] = useState<Record<string, any>>({});
  const [expandedMainId, setExpandedMainId] = useState<string | null>(null);

  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [isRightSidebarOpen, setIsRightSidebarOpen] = useState(false);
  const [liveTrainSearchText, setLiveTrainSearchText] = useState('');
  const [selectedZone, setSelectedZone] = useState('All');
  const [visibleTrainsCount, setVisibleTrainsCount] = useState(15);
  const [toStationId, setToStationId] = useState<string | null>(null);
  const [selectedPathIndex, setSelectedPathIndex] = useState(0);

  const [searchText, setSearchText] = useState(searchParams.get('train') || '');
  const [activeMainIndex, setActiveMainIndex] = useState(-1);
  const [activeFromIndex, setActiveFromIndex] = useState(-1);
  const [activeToIndex, setActiveToIndex] = useState(-1);
  const [fromSearchText, setFromSearchText] = useState(searchParams.get('from') || '');
  const [toSearchText, setToSearchText] = useState(searchParams.get('to') || '');
  const [isBottomCardExpanded, setIsBottomCardExpanded] = useState(false);

  const [mockTick, setMockTick] = useState(0);
  useEffect(() => {
    const interval = setInterval(() => {
      setMockTick(prev => prev + 1);
    }, 5000);
    return () => clearInterval(interval);
  }, []);

  const handleMapKeyDown = (
    e: React.KeyboardEvent,
    suggestions: any[],
    activeIndex: number,
    setActiveIndex: React.Dispatch<React.SetStateAction<number>>,
    onSelect: (item: any) => void
  ) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => (prev < suggestions.length - 1 ? prev + 1 : prev));
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => (prev > 0 ? prev - 1 : 0));
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < suggestions.length) {
        onSelect(suggestions[activeIndex]);
        setActiveIndex(-1);
      }
    }
  };

  const graphAdj = useMemo(() => buildGraph(stationsMeta), [stationsMeta]);

  const routePaths = useMemo(() => {
    if (!selectedStationId || !toStationId || !graphAdj || !stationsMeta) return [];
    return findPaths(graphAdj, selectedStationId, toStationId, 5, stationsMeta);
  }, [selectedStationId, toStationId, graphAdj, stationsMeta]);

  useEffect(() => {
    // Reset selected path index when route changes
    setSelectedPathIndex(0);
  }, [routePaths]);

  const suggestions = useMemo(() => {
    if (!searchText.trim()) return [];
    const lower = searchText.toLowerCase();
    return Object.entries(stationsMeta)
      .filter(([id, s]) => s.name.toLowerCase().includes(lower))
      .slice(0, 50); // limit to 50 suggestions
  }, [searchText, stationsMeta]);

  const fromSuggestions = useMemo(() => {
    if (!fromSearchText.trim()) return [];
    const lower = fromSearchText.toLowerCase();
    return Object.entries(stationsMeta)
      .filter(([id, s]) => s.name.toLowerCase().includes(lower))
      .slice(0, 50);
  }, [fromSearchText, stationsMeta]);

  const toSuggestions = useMemo(() => {
    if (!toSearchText.trim()) return [];
    const lower = toSearchText.toLowerCase();
    return Object.entries(stationsMeta)
      .filter(([id, s]) => s.name.toLowerCase().includes(lower))
      .slice(0, 50);
  }, [toSearchText, stationsMeta]);


  const [timetable, setTimetable] = useState<any>({});
  const [selectedTrain, setSelectedTrain] = useState<any>(null);
  const [liveTrainCoords, setLiveTrainCoords] = useState<[number, number] | null>(null);
  const [showAiModal, setShowAiModal] = useState(false);

let globalStationsMeta: any = null;
let globalTimetable: any = null;

  // Load GeoJSON and stations data
  useEffect(() => {
    if (globalStationsMeta && globalTimetable) {
      setStationsMeta(globalStationsMeta);
      setTimetable(globalTimetable);
      return;
    }
      
    if (globalStationsMeta) {
      setStationsMeta(globalStationsMeta);
    } else {
      fetch('/stations_metadata.json')
        .then(res => res.json())
        .then(data => {
          globalStationsMeta = data;
          setStationsMeta(data);
        });
    }
      
    if (globalTimetable) {
      setTimetable(globalTimetable);
    } else {
      fetch('/timetable.json')
        .then(res => res.json())
        .then(data => {
          for (const key of Object.keys(data)) {
            if (data[key] && data[key].s) {
              data[key].s.sort((a: any, b: any) => a[3] - b[3]);
            }
          }
          globalTimetable = data;
          setTimetable(data);
        })
        .catch(err => console.log('Timetable not found yet', err));
    }
  }, []);

  // Resolve searchParams from Dashboard
  useEffect(() => {
    if (Object.keys(stationsMeta).length === 0 || Object.keys(timetable).length === 0) return;
    
    const trainParam = searchParams.get('train');
    const fromParam = searchParams.get('from');
    const toParam = searchParams.get('to');
    
    if (trainParam && !selectedTrain) {
      if (timetable[trainParam]) {
        setSelectedTrain({
          train_number: trainParam,
          train_name: timetable[trainParam].n,
          dep_station: timetable[trainParam].s[0][0],
          arr_station: timetable[trainParam].s[timetable[trainParam].s.length - 1][0],
          delayMinutes: Math.floor(Math.random() * 45) - 15,
          currentStationIndex: Math.max(1, Math.floor(timetable[trainParam].s.length / 2)) // Train is halfway
        });
        
        const depNameNorm = normalizeStationName(timetable[trainParam].s[0][0]);
        const arrNameNorm = normalizeStationName(timetable[trainParam].s[timetable[trainParam].s.length - 1][0]);
        let fromId = null;
        let toId = null;
        for (const [id, meta] of Object.entries(stationsMeta)) {
          const metaNameNorm = normalizeStationName((meta as any).name);
          if (metaNameNorm === depNameNorm) fromId = id;
          if (metaNameNorm === arrNameNorm) toId = id;
        }
        if (fromId) {
           setSelectedStationId(fromId);
           setFromSearchText('');
        }
        if (toId) {
           setToStationId(toId);
           setToSearchText('');
        }
        
        setIsSidebarOpen(true);
      }
    } else if (fromParam && !selectedStationId) {
      let fromId = null;
      let toId = null;
      for (const [id, meta] of Object.entries(stationsMeta)) {
        if ((meta as any).name === fromParam) fromId = id;
        if (toParam && (meta as any).name === toParam) toId = id;
      }
      if (fromId) {
        setSelectedStationId(fromId);
        setIsSidebarOpen(true);
        if (toId) {
          setToStationId(toId);
        } else {
          const station = stationsMeta[fromId] as any;
          if (station && station.coordinates && mapRef.current) {
            mapRef.current.flyTo({ center: station.coordinates, zoom: 11, duration: 1500 });
          }
        }
      }
    }
  }, [stationsMeta, timetable, searchParams, selectedTrain, selectedStationId]);


  useEffect(() => {
    if (selectedTrain && timetable[selectedTrain.train_number]) {
      setTimeout(() => {
        const currentStationName = timetable[selectedTrain.train_number].s[selectedTrain.currentStationIndex]?.[0];
        const el = document.getElementById('train-station-' + currentStationName);
        if (el) el.scrollIntoView({ behavior: 'smooth', block: 'center' });
      }, 100);

      // Plot the train's route on the map
      if (stationsMeta) {
        const depNameNorm = normalizeStationName(selectedTrain.dep_station);
        const arrNameNorm = normalizeStationName(selectedTrain.arr_station);
        let fromId = null;
        let toId = null;
        for (const [id, meta] of Object.entries(stationsMeta)) {
          const mNorm = normalizeStationName((meta as any).name);
          if (mNorm === depNameNorm) fromId = id;
          if (mNorm === arrNameNorm) toId = id;
        }
        if (fromId) setSelectedStationId(fromId);
        if (toId) setToStationId(toId);
      }
    }
  }, [selectedTrain, stationsMeta]);

  // Live Train Interpolation
  useEffect(() => {
    if (selectedTrain && stationsMeta && timetable[selectedTrain.train_number]) {
      const stops = timetable[selectedTrain.train_number].s;
      
      const findCoords = (startIndex: number, step: number) => {
        let i = startIndex;
        while (i >= 0 && i < stops.length) {
          const nameNorm = normalizeStationName(stops[i][0]);
          for (const meta of Object.values(stationsMeta)) {
             if (normalizeStationName((meta as any).name) === nameNorm && (meta as any).coordinates) {
                return (meta as any).coordinates;
             }
          }
          i += step;
        }
        return null;
      };
      
      let currentCoords = findCoords(selectedTrain.currentStationIndex, -1);
      if (!currentCoords) currentCoords = findCoords(selectedTrain.currentStationIndex, 1);
      
      let nextCoords = findCoords(selectedTrain.currentStationIndex + 1, 1);
      if (!nextCoords) nextCoords = currentCoords;
      
      if (currentCoords && nextCoords) {
         setLiveTrainCoords(currentCoords);
         let progress = 0;
         const interval = setInterval(() => {
            progress += 0.005;
            if (progress > 1) progress = 0;
            const lng = currentCoords[0] + (nextCoords[0] - currentCoords[0]) * progress;
            const lat = currentCoords[1] + (nextCoords[1] - currentCoords[1]) * progress;
            setLiveTrainCoords([lng, lat]);
            console.log('Interpolating live train at:', [lng, lat]);
         }, 100);
         return () => clearInterval(interval);
      } else if (currentCoords) {
         setLiveTrainCoords(currentCoords);
      }
    } else {
      setLiveTrainCoords(null);
    }
  }, [selectedTrain, stationsMeta, timetable]);

  const onMouseMove = useCallback((event: any) => {
    const feature = event.features && event.features[0];
    if (feature && feature.layer.id.includes('-stations')) {
      setHoverInfo({
        feature,
        x: event.point.x,
        y: event.point.y
      });
    } else {
      setHoverInfo(null);
    }
  }, []);

  const onClick = useCallback((event: any) => {
    const feature = event.features && event.features[0];
    if (feature && feature.layer.id.includes('-stations')) {
      const stationId = feature.properties.stationId;
      setSelectedStationId(stationId);
      setToStationId(null);
      setIsSidebarOpen(true);
      setExpandedMainId(null);
      setSelectedTrain(null);
      setSearchParams({});
      if (feature.geometry && feature.geometry.coordinates) {
        mapRef.current?.flyTo({ center: feature.geometry.coordinates, zoom: 11, duration: 1500 });
      }
    } else {
      setSelectedStationId(null);
      setToStationId(null);
      setIsSidebarOpen(false);
      setExpandedMainId(null);
      setSelectedTrain(null);
      setSearchParams({});
    }
  }, [setSearchParams]);

  const selectedMeta = selectedStationId ? stationsMeta[selectedStationId] : null;
  const connectedBranches = useMemo(() => {
    if (!selectedMeta || !selectedMeta.connectedBranches) return [];
    return selectedMeta.connectedBranches;
  }, [selectedMeta]);

  // Create GeoJSON for the route line
  const routeGeoJSON = useMemo(() => {
    if (selectedTrain && timetable[selectedTrain.train_number] && stationsMeta) {
      const stops = timetable[selectedTrain.train_number].s;
      const coords: number[][] = [];
      for (const stop of stops) {
        const stationNameNorm = normalizeStationName(stop[0]);
        for (const meta of Object.values(stationsMeta)) {
           if (normalizeStationName((meta as any).name) === stationNameNorm && (meta as any).coordinates) {
              coords.push((meta as any).coordinates);
              break;
           }
        }
      }
      if (coords.length > 1) {
        return {
          type: 'FeatureCollection',
          features: [{
            type: 'Feature',
            properties: { isSelected: true },
            geometry: {
              type: 'LineString',
              coordinates: coords
            }
          }]
        };
      }
    } else if (toStationId && routePaths.length > 0) {
      const features: any[] = [];
      routePaths.forEach((path, idx) => {
        const isSelected = idx === selectedPathIndex;
        path.segments.forEach((seg: any) => {
          features.push({
            type: 'Feature',
            properties: { isSelected },
            geometry: {
              type: 'LineString',
              coordinates: seg.coords || []
            }
          });
        });
      });
      // Sort so selected is drawn on top
      features.sort((a, b) => (a.properties.isSelected ? 1 : 0) - (b.properties.isSelected ? 1 : 0));
      
      return {
        type: 'FeatureCollection',
        features
      };
    }
    
    // Fallback to showing all connected branches
    if (!selectedMeta || !selectedMeta.connectedBranches || selectedMeta.connectedBranches.length === 0) return null;
    
    const validBranches = selectedMeta.connectedBranches.filter((b: any) => b.trackCoords && b.trackCoords.length >= 2);
    if (validBranches.length === 0) return null;
    
    return {
      type: 'FeatureCollection',
      features: validBranches.map((branch: any) => ({
        type: 'Feature',
        properties: {},
        geometry: {
          type: 'LineString',
          coordinates: branch.trackCoords
        }
      }))
    };
  }, [selectedMeta, toStationId, routePaths, selectedPathIndex]);

  const memoizedMockTrains = useMemo(() => {
    let mockTrains: any[] = liveTrains;
    if (!liveTrains || liveTrains.length === 0) {
      if (!timetable || Object.keys(timetable).length === 0) return [];
      
      const uniqueNames = new Set();
      const uniqueTrains = [];
      for (const [id, t] of Object.entries(timetable)) {
         if (!uniqueNames.has((t as any).n)) {
            uniqueNames.add((t as any).n);
            uniqueTrains.push([id, t]);
         }
         if (uniqueTrains.length >= 100) break;
      }
      
      mockTrains = uniqueTrains.map(([id, t]: [string, any], index) => {
        const stops = t.s;
        const randDelay = Math.floor(Math.sin(index + mockTick) * 30);
        const currStopIdx = Math.floor(stops.length / 2);
        const currentStopName = stops[currStopIdx]?.[0] || '';
        
        let coords = [0, 0];
        const nameNorm = normalizeStationName(currentStopName);
        for (const meta of Object.values(stationsMeta)) {
           if (normalizeStationName((meta as any).name) === nameNorm && (meta as any).coordinates) {
              coords = (meta as any).coordinates;
              break;
           }
        }
        
        const speed = 75 + (index % 20) + (Math.sin(mockTick + index) * 5);
        
        let zone = 'Central';
        if (coords[1] > 26) zone = 'Northern';
        else if (coords[1] < 18) zone = 'Southern';
        else if (coords[0] > 82) zone = 'Eastern';
        else if (coords[0] < 75) zone = 'Western';
        
        return {
          id,
          name: t.n,
          scheduledEta: stops[stops.length-1]?.[1] || 'N/A',
          aiEta: stops[stops.length-1]?.[1] || 'N/A',
          delayMin: randDelay > 0 ? randDelay : 0,
          currentLocation: coords,
          currentLocationName: currentStopName || 'En route',
          currentSpeed: speed,
          confidence: 85 + (index % 10),
          zone
        };
      });
    } else {
       const uniqueNames = new Set();
       const deduplicatedLiveTrains = [];
       for (const train of liveTrains) {
         if (!uniqueNames.has(train.name)) {
            uniqueNames.add(train.name);
            
            let zone = 'Central';
            if (Array.isArray(train.currentLocation) && train.currentLocation.length === 2) {
               const coords = train.currentLocation;
               if (coords[1] > 26) zone = 'Northern';
               else if (coords[1] < 18) zone = 'Southern';
               else if (coords[0] > 82) zone = 'Eastern';
               else if (coords[0] < 75) zone = 'Western';
            }
            
            deduplicatedLiveTrains.push({...train, zone});
         }
       }
       mockTrains = deduplicatedLiveTrains;
    }
    return mockTrains;
  }, [liveTrains, timetable, stationsMeta, mockTick]);

  // Heatmap GeoJSON for Traffic Density (Live Trains)
  const busyRoutesGeoJSON = useMemo(() => {
    if (!memoizedMockTrains || memoizedMockTrains.length === 0) return null;
    const features = memoizedMockTrains
      .filter((t: any) => Array.isArray(t.currentLocation) && t.currentLocation.length === 2 && !isNaN(t.currentLocation[0]) && !isNaN(t.currentLocation[1]))
      .map((t: any) => ({
        type: 'Feature',
        properties: { weight: t.delayMin > 20 ? 1 : 0.5 },
        geometry: {
          type: 'Point',
          coordinates: t.currentLocation
        }
      }));
    return {
      type: 'FeatureCollection',
      features
    };
  }, [memoizedMockTrains]);

  // Fit bounds when a route is generated
  useEffect(() => {
    if ((toStationId || selectedTrain) && routeGeoJSON && routeGeoJSON.features && routeGeoJSON.features.length > 0 && mapRef.current) {
      let minLng = Infinity;
      let minLat = Infinity;
      let maxLng = -Infinity;
      let maxLat = -Infinity;
      let hasCoords = false;

      routeGeoJSON.features.forEach((f: any) => {
        if (f.geometry && f.geometry.coordinates) {
          f.geometry.coordinates.forEach((coord: number[]) => {
            if (coord[0] < minLng) minLng = coord[0];
            if (coord[1] < minLat) minLat = coord[1];
            if (coord[0] > maxLng) maxLng = coord[0];
            if (coord[1] > maxLat) maxLat = coord[1];
            hasCoords = true;
          });
        }
      });

      if (hasCoords) {
        mapRef.current.fitBounds(
          [
            [minLng, minLat],
            [maxLng, maxLat]
          ],
          { padding: { top: 60, bottom: 60, left: 420, right: 60 }, duration: 1500 }
        );
      }
    }
  }, [toStationId, routeGeoJSON]);

  return (
    <div style={{ width: '100%', height: '100%', position: 'relative' }}>
      <Map
        ref={mapRef}
        initialViewState={{
          longitude: 76.5,
          latitude: 30.0,
          zoom: 6,
          pitch: 0,
        }}
        mapStyle={mapStyle as any}
        mapLib={maplibregl as any}
        attributionControl={false}
        interactiveLayerIds={
          ['central-zone', 'eastern-zone', 'north-eastern-zone', 'northern-zone', 'southern-zone', 'western-zone'].flatMap(zone => [
            `${zone}-stations-main`, 
            `${zone}-stations-middle`, 
            `${zone}-stations-glow-main`, 
            `${zone}-stations-glow-middle`
          ])
        }
        onMouseMove={onMouseMove}
        onClick={onClick}
        cursor={hoverInfo ? 'pointer' : 'grab'}
      >
        {/* Render a Source and Layers for each zone */}
        {['central-zone', 'eastern-zone', 'north-eastern-zone', 'northern-zone', 'southern-zone', 'western-zone'].map((zone) => (
          <Source key={zone} id={`${zone}-source`} type="geojson" data={`/${zone}_real.geojson`} tolerance={3.0} buffer={32} lineMetrics={false}>
            <Layer
              id={`${zone}-tracks`}
              type="line"
              filter={['==', 'type', 'track']}
              paint={{
                'line-color': '#94a3b8',
                'line-width': [
                  'interpolate', ['linear'], ['zoom'],
                  5, 1,    // zoom 5: 1px width
                  10, 3    // zoom 10: 3px width
                ],
                'line-opacity': 0.7,
              }}
            />
            {/* Main Station Glow Effect */}
            <Layer
              id={`${zone}-stations-glow-main`}
              type="circle"
              filter={['all', ['==', 'type', 'station'], ['==', 'stationClass', 'main']]}
              minzoom={6}
              paint={{
                'circle-radius': [
                  'interpolate', ['linear'], ['zoom'],
                  6, 3,     // zoom 6: faint glow
                  9, 8,     // zoom 9: medium glow
                  14, 20    // zoom 14: large glow
                ],
                'circle-color': '#f59e0b', // Darker Amber glow for main stations
                'circle-blur': 1,
                'circle-opacity': 0.7,
              }}
            />
            {/* Main Station Core */}
            <Layer
              id={`${zone}-stations-main`}
              type="circle"
              filter={['all', ['==', 'type', 'station'], ['==', 'stationClass', 'main']]}
              minzoom={6}
              paint={{
                'circle-radius': [
                  'interpolate', ['linear'], ['zoom'],
                  6, 2,     // zoom 6: tiny core
                  9, 4,     // zoom 9: small dot
                  14, 8     // zoom 14: large dot
                ],
                'circle-color': '#ffffff', // White core for main stations
                'circle-stroke-width': [
                  'interpolate', ['linear'], ['zoom'],
                  6, 1,
                  12, 2
                ],
                'circle-stroke-color': '#78350f', // Dark amber stroke
              }}
            />
            {/* Middle Station Glow Effect */}
            <Layer
              id={`${zone}-stations-glow-middle`}
              type="circle"
              filter={['all', ['==', 'type', 'station'], ['==', 'stationClass', 'middle']]}
              minzoom={8.5} // Completely hidden until zoomed into a specific state/region
              paint={{
                'circle-radius': [
                  'interpolate', ['linear'], ['zoom'],
                  8.5, 2,   // zoom 8.5: faint glow
                  11, 6,    // zoom 11: medium glow
                  14, 12    // zoom 14: large glow
                ],
                'circle-color': '#fbbf24', // Amber glow
                'circle-blur': 1,
                'circle-opacity': 0.5,
              }}
            />
            {/* Middle Station Core */}
            <Layer
              id={`${zone}-stations-middle`}
              type="circle"
              filter={['all', ['==', 'type', 'station'], ['==', 'stationClass', 'middle']]}
              minzoom={8.5}
              paint={{
                'circle-radius': [
                  'interpolate', ['linear'], ['zoom'],
                  8.5, 1.5, // zoom 8.5: tiny core
                  11, 2.5,  // zoom 11: small dot
                  14, 5     // zoom 14: large dot
                ],
                'circle-color': '#fef3c7', // Very light yellow core
                'circle-stroke-width': [
                  'interpolate', ['linear'], ['zoom'],
                  8.5, 0.5,
                  12, 1
                ],
                'circle-stroke-color': '#78350f', // Dark amber stroke
              }}
            />
          </Source>
        ))}

        {routeGeoJSON && (
          <>
            {/* Draw the connected tracks on top */}
            <Source id="route" type="geojson" data={routeGeoJSON as any}>
              <Layer
                id="route-line-base"
                type="line"
                paint={{
                  'line-color': [
                    'case',
                    ['boolean', ['get', 'isSelected'], true],
                    selectedTrain ? (selectedTrain.delayMinutes > 20 ? '#ef4444' : (selectedTrain.delayMinutes > 0 ? '#f59e0b' : '#1e40af')) : '#1e40af', // Darker base
                    '#64748b' // Dark grey for alternative
                  ],
                  'line-width': [
                    'case',
                    ['boolean', ['get', 'isSelected'], true],
                    6,
                    3
                  ],
                  'line-opacity': 0.9,
                }}
              />
              <Layer
                id="route-line-dash"
                type="line"
                paint={{
                  'line-color': [
                    'case',
                    ['boolean', ['get', 'isSelected'], true],
                    selectedTrain ? (selectedTrain.delayMinutes > 20 ? '#fca5a5' : (selectedTrain.delayMinutes > 0 ? '#fde68a' : '#93c5fd')) : '#93c5fd', // Lighter dash
                    '#cbd5e1'
                  ],
                  'line-width': [
                    'case',
                    ['boolean', ['get', 'isSelected'], true],
                    3,
                    1
                  ],
                  'line-dasharray': [2, 2],
                  'line-opacity': 1,
                }}
              />
            </Source>

            {/* Markers for FROM and TO stations */}
            {selectedStationId && stationsMeta[selectedStationId] && stationsMeta[selectedStationId].coordinates && (
              <Marker
                longitude={stationsMeta[selectedStationId].coordinates[0]}
                latitude={stationsMeta[selectedStationId].coordinates[1]}
                anchor="bottom"
                offset={[0, -4]}
              >
                <div className="teardrop-marker">
                  <div className="teardrop-inner"></div>
                </div>
              </Marker>
            )}

            {toStationId && stationsMeta[toStationId] && stationsMeta[toStationId].coordinates && (
              <Marker
                longitude={stationsMeta[toStationId].coordinates[0]}
                latitude={stationsMeta[toStationId].coordinates[1]}
                anchor="center"
              >
                <div className="double-circle-marker">
                  <div className="double-circle-pulse"></div>
                  <div className="double-circle-middle">
                    <div className="double-circle-core"></div>
                  </div>
                </div>
              </Marker>
            )}

          </>
        )}

        {showDensityHeatmap && busyRoutesGeoJSON && (
          <Source id="busy-routes-heatmap-source" type="geojson" data={busyRoutesGeoJSON as any}>
            <Layer
              id="busy-routes-heatmap-layer"
              type="heatmap"
              paint={{
                'heatmap-weight': [
                  'interpolate', ['linear'], ['get', 'weight'],
                  0, 0,
                  1, 1
                ],
                'heatmap-intensity': [
                  'interpolate', ['linear'], ['zoom'],
                  0, 1,
                  15, 3
                ],
                'heatmap-color': [
                  'interpolate', ['linear'], ['heatmap-density'],
                  0, 'rgba(33,102,172,0)',
                  0.2, 'rgb(103,169,207)',
                  0.4, 'rgb(209,229,240)',
                  0.6, 'rgb(253,219,199)',
                  0.8, 'rgb(239,138,98)',
                  1, 'rgb(178,24,43)'
                ],
                'heatmap-radius': [
                  'interpolate', ['linear'], ['zoom'],
                  0, 15,
                  9, 30,
                  15, 60
                ],
                'heatmap-opacity': 0.8,
              }}
            />
          </Source>
        )}

        {liveTrains && liveTrains.filter(t => Array.isArray(t.currentLocation) && t.currentLocation.length === 2 && !isNaN((t.currentLocation as any)[0]) && !isNaN((t.currentLocation as any)[1])).map(train => (
          <Marker
            key={train.id}
            longitude={(train.currentLocation as any)[0]}
            latitude={(train.currentLocation as any)[1]}
            anchor="center"
          >
            <div style={{
              background: 'white',
              borderRadius: '50%',
              padding: '4px',
              boxShadow: '0 2px 8px rgba(0,0,0,0.2)',
              border: `2px solid ${train.delayMin > 20 ? '#ef4444' : (train.delayMin > 0 ? '#f59e0b' : '#10b981')}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              cursor: 'pointer'
            }}
            onClick={(e) => {
              (e as any).originalEvent.stopPropagation();
              // Navigate to dashboard and search for this train, or select it directly
              // if it exists in the hardcoded timetable
              if (timetable[train.id]) {
                setSelectedTrain({
                  ...timetable[train.id],
                  train_number: train.id,
                  train_name: train.name,
                  dep_station: timetable[train.id].s[0][0],
                  arr_station: timetable[train.id].s[timetable[train.id].s.length - 1][0],
                  delayMinutes: train.delayMin,
                  currentStationIndex: Math.max(1, Math.floor((timetable[train.id]?.s?.length || 2) / 2))
                });
                setIsSidebarOpen(true);
              }
            }}>
              <Train size={14} color={train.delayMin > 20 ? '#ef4444' : (train.delayMin > 0 ? '#f59e0b' : '#10b981')} />
            </div>
          </Marker>
        ))}

        {liveTrainCoords && !isNaN(liveTrainCoords[0]) && !isNaN(liveTrainCoords[1]) && (
          <Marker
            longitude={liveTrainCoords[0]}
            latitude={liveTrainCoords[1]}
            anchor="center"
          >
            <div className="train-marker-animated" style={{
              background: 'white',
              borderRadius: '50%',
              padding: '6px',
              boxShadow: '0 4px 12px rgba(0,0,0,0.3)',
              border: `2px solid ${selectedTrain?.delayMinutes > 20 ? '#ef4444' : '#10b981'}`,
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center'
            }}>
              <Train size={18} color={selectedTrain?.delayMinutes > 20 ? '#ef4444' : '#10b981'} />
            </div>
          </Marker>
        )}
      </Map>

      {/* Back to Dashboard Button */}
      <div 
        onClick={() => navigate('/')}
        style={{
          position: 'absolute',
          top: '20px',
          left: '20px',
          transition: 'all 0.3s ease',
          zIndex: 0,
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '8px',
          padding: '8px 16px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          cursor: 'pointer',
          fontWeight: 600,
          color: '#0f172a',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(0, 0, 0, 0.05)'
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}
      >
        <ArrowLeft size={18} />
        
      </div>

      {/* Traffic Density Toggle Button */}
      <div 
        onClick={() => setShowDensityHeatmap(!showDensityHeatmap)}
        style={{
          position: 'absolute',
          bottom: '40px',
          left: '20px',
          transition: 'all 0.3s ease',
          zIndex: 0,
          background: showDensityHeatmap ? '#ef4444' : 'rgba(255, 255, 255, 0.95)',
          borderRadius: '8px',
          padding: '8px 16px',
          boxShadow: '0 4px 12px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          alignItems: 'center',
          gap: '8px',
          cursor: 'pointer',
          fontWeight: 600,
          color: showDensityHeatmap ? '#ffffff' : '#0f172a',
          backdropFilter: 'blur(12px)',
          border: showDensityHeatmap ? '1px solid #ef4444' : '1px solid rgba(0, 0, 0, 0.05)'
        }}
        onMouseEnter={(e) => e.currentTarget.style.transform = 'translateY(-2px)'}
        onMouseLeave={(e) => e.currentTarget.style.transform = 'none'}
      >
        <Activity size={18} />
        {showDensityHeatmap ? 'Traffic Density' : 'Traffic Density'}
      </div>

      {/* Left Sidebar Toggle Handle */}
      <div 
        onClick={() => setIsSidebarOpen(!isSidebarOpen)}
        style={{
          position: 'absolute',
          top: '50%',
          left: isSidebarOpen ? '380px' : '0',
          transform: 'translateY(-50%)',
          transition: 'left 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          zIndex: 60,
          background: '#ffffff',
          borderTopRightRadius: '8px',
          borderBottomRightRadius: '8px',
          padding: '16px 8px',
          boxShadow: '4px 0 12px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          color: '#64748b',
          border: '1px solid rgba(0, 0, 0, 0.05)',
          borderLeft: 'none'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = '#3b82f6';
          e.currentTarget.style.background = '#f8fafc';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = '#64748b';
          e.currentTarget.style.background = '#ffffff';
        }}
      >
        {isSidebarOpen ? <ChevronLeft size={24} /> : <ChevronRight size={24} />}
      </div>

      {/* Right Sidebar Toggle Handle */}
      <div 
        onClick={() => setIsRightSidebarOpen(!isRightSidebarOpen)}
        style={{
          position: 'absolute',
          top: '50%',
          right: isRightSidebarOpen ? '380px' : '0',
          transform: 'translateY(-50%)',
          transition: 'right 0.3s cubic-bezier(0.4, 0, 0.2, 1)',
          zIndex: 60,
          background: '#ffffff',
          borderTopLeftRadius: '8px',
          borderBottomLeftRadius: '8px',
          padding: '16px 8px',
          boxShadow: '-4px 0 12px rgba(0, 0, 0, 0.1)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          cursor: 'pointer',
          color: '#64748b',
          border: '1px solid rgba(0, 0, 0, 0.05)',
          borderRight: 'none'
        }}
        onMouseEnter={(e) => {
          e.currentTarget.style.color = '#3b82f6';
          e.currentTarget.style.background = '#f8fafc';
        }}
        onMouseLeave={(e) => {
          e.currentTarget.style.color = '#64748b';
          e.currentTarget.style.background = '#ffffff';
        }}
      >
        {isRightSidebarOpen ? <ChevronRight size={24} /> : <ChevronLeft size={24} />}
      </div>

      {/* Search Bar */}
      <div
        style={{
          position: 'absolute',
          top: '20px',
          left: '50%',
          transform: 'translateX(-50%)',
          width: '400px',
          maxWidth: '90vw',
          zIndex: 60,
          background: 'rgba(255, 255, 255, 0.95)',
          borderRadius: '12px',
          boxShadow: '0 8px 24px rgba(0, 0, 0, 0.12)',
          display: 'flex',
          flexDirection: 'column',
          backdropFilter: 'blur(12px)',
          border: '1px solid rgba(0, 0, 0, 0.05)'
        }}
      >
        <div style={{ display: 'flex', alignItems: 'center', padding: '12px 16px' }}>
          <Menu size={20} style={{ color: '#64748b', marginRight: '12px', cursor: 'pointer' }} />
          <input
            type="text"
            placeholder="Search Train or Station"
            value={searchText}
            onKeyDown={(e) => handleMapKeyDown(e, suggestions, activeMainIndex, setActiveMainIndex, ([id, station]) => {
              setSelectedStationId(id);
              setToStationId(null);
              setExpandedMainId(null);
              setSearchText('');
              setIsSidebarOpen(true);
              if (station.coordinates) {
                mapRef.current?.flyTo({ center: station.coordinates, zoom: 11, duration: 1500 });
              }
            })}
            onChange={(e) => {
              setSearchText(e.target.value);
              setActiveMainIndex(-1);
            }}
            style={{
              flex: 1,
              background: 'transparent',
              border: 'none',
              color: '#0f172a',
              fontSize: '16px',
              outline: 'none',
            }}
          />
          {searchText ? (
            <X size={20} style={{ color: '#64748b', cursor: 'pointer' }} onClick={() => setSearchText('')} />
          ) : (
            <Search size={20} style={{ color: '#64748b', cursor: 'pointer' }} />
          )}
        </div>
        
        {searchText && suggestions.length > 0 && (
          <div style={{ borderTop: '1px solid #e2e8f0', maxHeight: '250px', overflowY: 'auto', padding: '8px 0' }}>
            {suggestions.map(([id, station], idx) => (
              <div 
                key={id}
                onMouseEnter={() => setActiveMainIndex(idx)}
                onClick={() => {
                  setSelectedStationId(id);
                  setToStationId(null);
                  setExpandedMainId(null);
                  setSearchText('');
                  setIsSidebarOpen(true);
                  if (station.coordinates) {
                    mapRef.current?.flyTo({ center: station.coordinates, zoom: 11, duration: 1500 });
                  }
                }}
                style={{
                  padding: '10px 16px',
                  cursor: 'pointer',
                  color: '#334155',
                  fontSize: '14px',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  background: activeMainIndex === idx ? '#f1f5f9' : 'transparent'
                }}
                onMouseOver={(e) => { if (activeMainIndex !== idx) e.currentTarget.style.background = '#f1f5f9' }}
                onMouseOut={(e) => { if (activeMainIndex !== idx) e.currentTarget.style.background = 'transparent' }}
              >
                <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: station.stationClass === 'main' ? '#f59e0b' : '#94a3b8' }}></div>
                {station.name}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Custom Zoom Controls */}
      <div style={{ position: 'absolute', right: '20px', bottom: '30px', display: 'flex', flexDirection: 'column', gap: '8px', zIndex: 10 }}>
        <button
          onClick={() => mapRef.current?.zoomIn({ duration: 300 })}
          className="glass-panel"
          style={{ width: '40px', height: '40px', display: 'flex', justifyContent: 'center', alignItems: 'center', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', cursor: 'pointer' }}
          title="Zoom In"
        >
          <Plus size={20} />
        </button>
        <button
          onClick={() => mapRef.current?.zoomOut({ duration: 300 })}
          className="glass-panel"
          style={{ width: '40px', height: '40px', display: 'flex', justifyContent: 'center', alignItems: 'center', border: '1px solid var(--glass-border)', color: 'var(--text-primary)', cursor: 'pointer' }}
          title="Zoom Out"
        >
          <Minus size={20} />
        </button>
      </div>

      {/* Sidebar for Selected Station */}
      {isSidebarOpen && (
        <div style={{
          position: 'absolute',
          left: 0,
          top: 0,
          bottom: 0,
          width: '380px',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(8px)',
          boxShadow: '4px 0 25px rgba(0,0,0,0.1)',
          padding: selectedTrain ? 0 : '24px',
          overflowY: selectedTrain ? 'hidden' : 'auto',
          display: selectedTrain ? 'flex' : 'block',
          flexDirection: 'column',
          zIndex: 50,
          borderRight: '1px solid rgba(0,0,0,0.05)',
          color: '#1e293b'
        }}>
          {selectedTrain ? (
            <div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
              <div style={{ 
                display: 'flex', 
                alignItems: 'flex-start', 
                padding: '24px 24px 16px 24px', 
                borderBottom: '1px solid #e2e8f0',
                background: '#ffffff',
                zIndex: 10,
                flexShrink: 0
              }}>
                <button 
                  onClick={() => {
                    setSelectedTrain(null);
                    setSelectedStationId(null);
                    setToStationId(null);
                    setSearchParams({});
                  }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', padding: '4px', marginRight: '12px', display: 'flex', alignItems: 'center', justifyContent: 'center', marginTop: '2px' }}
                >
                  <ArrowLeft size={20} color="#64748b" />
                </button>
                <div style={{ flex: 1 }}>
                  <h2 style={{ margin: '0 0 6px 0', fontSize: '18px', fontWeight: 800, color: '#0f172a', lineHeight: 1.2 }}>{selectedTrain.train_name}</h2>
                  <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                    <div style={{ background: '#e0e7ff', color: '#4f46e5', fontWeight: 700, fontSize: '12px', padding: '2px 6px', borderRadius: '4px' }}>
                      {selectedTrain.train_number}
                    </div>
                    <span style={{ fontSize: '13px', color: '#64748b', fontWeight: 600 }}>Scheduled Running</span>
                  </div>
                </div>
                <button 
                  onClick={() => setShowAiModal(true)}
                  style={{ background: '#eff6ff', color: '#2563eb', border: '1px solid #bfdbfe', borderRadius: '8px', padding: '8px 12px', fontWeight: 700, fontSize: '12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  <Target size={16} /> AI Route
                </button>
              </div>
              
              <div style={{ display: 'flex', alignItems: 'center', padding: '12px 24px', backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', fontSize: '11px', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase' }}>
                <div style={{ width: '60px', textAlign: 'right' }}>ARRIVAL</div>
                <div style={{ width: '32px', margin: '0 8px' }}></div>
                <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div style={{ backgroundColor: '#f1f5f9', padding: '4px 12px', borderRadius: '12px', color: '#475569', border: '1px solid #e2e8f0', display: 'inline-block' }}>DAY 1 • {new Date().toLocaleDateString('en-US', {day:'numeric', month:'short'}).toUpperCase()}</div>
                  <div style={{ textAlign: 'right' }}>DEPARTURE</div>
                </div>
              </div>
              
              <div style={{ paddingLeft: '24px', paddingRight: '24px', paddingTop: '24px', paddingBottom: '200px', overflowY: 'auto', flex: 1, backgroundColor: '#ffffff' }}>
                <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {/* The Track */}
                  <div style={{ 
                    position: 'absolute', 
                    left: '76px', // 60px time + 8px margin + 16px half-width - 8px track half-width
                    boxSizing: 'border-box',
                    top: '12px', 
                    bottom: '20px', 
                    width: '16px', 
                    zIndex: 1,
                    borderLeft: '3px solid #cbd5e1',
                    borderRight: '3px solid #cbd5e1',
                    backgroundImage: 'repeating-linear-gradient(to bottom, transparent, transparent 10px, #cbd5e1 10px, #cbd5e1 13px)'
                  }}></div>
                  
                  {timetable[selectedTrain.train_number]?.s.map((stop: any, idx: number) => {
                  const formatTime = (timeStr: string) => {
                    if (!timeStr) return '';
                    const [h, m] = timeStr.split(':');
                    let hours = parseInt(h, 10);
                    const ampm = hours >= 12 ? 'PM' : 'AM';
                    hours = hours % 12 || 12;
                    return `${hours}:${m}${ampm}`;
                  };
                  
                  const addDelay = (timeStr: string, delayMin: number) => {
                    if (!timeStr) return '';
                    const [h, m] = timeStr.split(':');
                    const date = new Date();
                    date.setHours(parseInt(h, 10));
                    date.setMinutes(parseInt(m, 10) + delayMin);
                    
                    let hours = date.getHours();
                    const ampm = hours >= 12 ? 'PM' : 'AM';
                    hours = hours % 12 || 12;
                    const mins = date.getMinutes().toString().padStart(2, '0');
                    return `${hours}:${mins}${ampm}`;
                  };

                  const isFirst = idx === 0;
                  const isLast = idx === timetable[selectedTrain.train_number].s.length - 1;
                  const isPassed = idx < selectedTrain.currentStationIndex;
                  const isCurrent = idx === selectedTrain.currentStationIndex;
                  const isFuture = idx > selectedTrain.currentStationIndex;
                  
                  const isDelayed = selectedTrain.delayMinutes > 0 && (isCurrent || isFuture);
                  const isEarly = selectedTrain.delayMinutes < 0 && (isCurrent || isFuture);
                  const displayColor = isDelayed ? '#ef4444' : (isEarly ? '#2563eb' : '#334155');
                  
                  const arrTimeRaw = isFirst ? stop[2] : stop[1];
                  const depTimeRaw = isLast ? stop[1] : stop[2];
                  
                  const arrTime = formatTime(arrTimeRaw);
                  const depTime = formatTime(depTimeRaw);
                  const arrTimeLive = (isDelayed || isEarly) ? addDelay(arrTimeRaw, selectedTrain.delayMinutes) : '';
                  const depTimeLive = (isDelayed || isEarly) ? addDelay(depTimeRaw, selectedTrain.delayMinutes) : '';
                  
                  // Mock platform data for screenshot accuracy
                  const pfNumber = (idx % 6) + 1;
                  
                  return (
                    <div id={`train-station-${stop[0]}`} key={idx} style={{ display: 'flex', alignItems: 'flex-start', position: 'relative', zIndex: 2 }}>
                      
                      {/* Left: Time */}
                      <div style={{ width: '60px', textAlign: 'right', display: 'flex', flexDirection: 'column', paddingTop: '2px' }}>
                         <div style={{ fontSize: '13px', fontWeight: 600, color: '#334155' }}>
                            {arrTime}
                         </div>
                         {(isDelayed || isEarly) && (
                            <div style={{ fontSize: '13px', fontWeight: 600, color: displayColor, marginTop: '2px' }}>
                              {arrTimeLive}
                            </div>
                         )}
                      </div>

                      {/* Middle: Dot / Train Icon */}
                      <div style={{ width: '32px', display: 'flex', justifyContent: 'center', margin: '0 8px', paddingTop: isCurrent ? '0px' : '4px' }}>
                        {isCurrent ? (
                           <div className="train-marker-animated" style={{
                              width: '26px', height: '26px', borderRadius: '50%',
                              backgroundColor: '#3b82f6', // Bright blue
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              boxShadow: isDelayed ? '0 0 0 6px rgba(239, 68, 68, 0.15)' : (isEarly ? '0 0 0 6px rgba(37, 99, 235, 0.15)' : '0 0 0 6px rgba(51, 65, 85, 0.1)'),
                              zIndex: 3
                           }}>
                              <Train size={14} color="#ffffff" />
                           </div>
                        ) : (
                           <div style={{ 
                             width: '12px', height: '12px', borderRadius: '50%', 
                             background: isPassed ? '#10b981' : '#eab308', 
                             border: '2px solid #ffffff',
                             boxShadow: '0 0 0 1px #e2e8f0', // Slight border to make dot stand out from track
                             zIndex: 3
                           }}></div>
                        )}
                      </div>
                      
                      {/* Right: Station Info */}
                      <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                        <div style={{ display: 'flex', flexDirection: 'column' }}>
                          <div style={{ fontSize: '15px', fontWeight: (isFirst || isLast || isCurrent) ? 800 : 600, color: '#0f172a' }}>
                            {stop[0]}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 600, display: 'flex', alignItems: 'center', gap: '6px', marginTop: '6px' }}>
                            CODE • {stop[3]} km
                            <span style={{ backgroundColor: '#f1f5f9', border: '1px solid #e2e8f0', color: '#3b82f6', padding: '1px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 800 }}>PF {pfNumber}</span>
                          </div>
                        </div>
                        
                        {/* Far Right: Departure Time */}
                        <div style={{ textAlign: 'right', paddingTop: '2px' }}>
                          <div style={{ fontSize: '13px', fontWeight: 600, color: '#334155' }}>
                            {depTime}
                          </div>
                          {(isDelayed || isEarly) && (
                            <div style={{ fontSize: '13px', fontWeight: 600, color: displayColor, marginTop: '2px' }}>
                              {depTimeLive}
                            </div>
                          )}
                        </div>
                      </div>
                    </div>
                  );
                })}
                </div>
              </div>

              {/* Fixed Bottom Live Overlay Card */}
              <div style={{ 
                position: 'absolute', bottom: 0, left: 0, right: 0, 
                backgroundColor: '#ffffff', color: '#0f172a', 
                borderTopLeftRadius: '24px', borderTopRightRadius: '24px', 
                padding: '20px 16px', boxShadow: '0 -8px 30px rgba(0,0,0,0.2)', zIndex: 10 
              }}>
                <div 
                  style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', cursor: 'pointer' }}
                  onClick={() => setIsBottomCardExpanded(!isBottomCardExpanded)}
                >
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>Departed {timetable[selectedTrain.train_number]?.s[Math.max(0, selectedTrain.currentStationIndex-1)]?.[0] || 'Origin'}</h3>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '6px' }}>
                      <span style={{ backgroundColor: '#2563eb', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 800 }}>
                        {selectedTrain.delayMinutes > 0 ? `${selectedTrain.delayMinutes}M LATE` : (selectedTrain.delayMinutes < 0 ? `${Math.abs(selectedTrain.delayMinutes)}M EARLY` : 'ON TIME')}
                      </span>
                      <span style={{ fontSize: '12px', color: '#64748b', fontWeight: 600 }}>Updated 1 minute ago</span>
                    </div>
                  </div>
                  <div style={{ display: 'flex', gap: '12px', alignItems: 'center' }}>
                    {isBottomCardExpanded ? <ChevronDown size={24} color="#64748b" /> : <ChevronUp size={24} color="#64748b" />}
                    <div 
                      style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: '#2563eb', display: 'flex', justifyContent: 'center', alignItems: 'center', cursor: 'pointer', boxShadow: '0 4px 10px rgba(37,99,235,0.3)' }}
                      onClick={(e) => e.stopPropagation()}
                    >
                      <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path></svg>
                    </div>
                  </div>
                </div>

                {isBottomCardExpanded && (
                  <div style={{ border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden', marginTop: '16px' }}>
                    <div style={{ padding: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #e2e8f0' }}>
                      <span style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a' }}>{selectedTrain.dep_station}</span>
                      <div style={{ flex: 1, margin: '0 12px', position: 'relative', height: '4px', backgroundColor: '#e2e8f0', borderRadius: '2px' }}>
                        <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '60%', backgroundColor: '#2563eb', borderRadius: '2px' }}></div>
                        <div style={{ position: 'absolute', left: '60%', top: '-6px', width: '16px', height: '16px', borderRadius: '50%', border: '2px solid #2563eb', backgroundColor: '#ffffff', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: 'translateX(-50%)' }}>
                           <Train size={8} color="#2563eb" />
                        </div>
                      </div>
                      <span style={{ fontSize: '12px', fontWeight: 700, color: '#0f172a' }}>{selectedTrain.arr_station}</span>
                    </div>
                    
                    <div style={{ display: 'flex', backgroundColor: '#f8fafc' }}>
                      <div style={{ flex: 1, padding: '12px', borderRight: '1px solid #e2e8f0', textAlign: 'center' }}>
                        <div style={{ fontSize: '10px', fontWeight: 700, color: '#64748b', marginBottom: '4px', textTransform: 'uppercase' }}>Next Stop</div>
                        <div style={{ fontSize: '14px', fontWeight: 800, color: '#0f172a', marginBottom: '4px' }}>{timetable[selectedTrain.train_number]?.s[selectedTrain.currentStationIndex]?.[0] || 'Destination'}</div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>15km • {new Date().toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'})}</div>
                      </div>
                      <div style={{ flex: 1, padding: '12px', textAlign: 'center' }}>
                        <div style={{ fontSize: '10px', fontWeight: 700, color: '#64748b', marginBottom: '4px', textTransform: 'uppercase' }}>To Reach</div>
                        <div style={{ fontSize: '14px', fontWeight: 800, color: '#0f172a', marginBottom: '4px' }}>{selectedTrain.arr_station}</div>
                        <div style={{ fontSize: '11px', color: '#64748b' }}>850km • 8:45AM</div>
                      </div>
                    </div>
                    <div style={{ backgroundColor: '#dcfce7', color: '#15803d', textAlign: 'center', padding: '8px', fontSize: '12px', fontWeight: 700 }}>
                      ✓ Running {selectedTrain.delayMinutes === 0 ? 'On Time' : (selectedTrain.delayMinutes > 0 ? `${selectedTrain.delayMinutes}m Late` : `${Math.abs(selectedTrain.delayMinutes)}m Early`)}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                  {toStationId && (
                    <button
                      onClick={() => {
                        setToStationId(null);
                        setToSearchText('');
                      }}
                      style={{ background: 'none', border: 'none', cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4px', color: '#64748b' }}
                      title="Go Back"
                    >
                      <ArrowLeft size={20} />
                    </button>
                  )}
                  <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700 }}>Station Explorer</h2>
                </div>
                <button 
                  onClick={() => { setSelectedStationId(null); setToStationId(null); setIsSidebarOpen(false); setSelectedTrain(null); setSearchParams({}); }}
                  style={{ background: 'none', border: 'none', cursor: 'pointer', fontSize: '18px', color: '#94a3b8' }}
                >
                  <X size={20} />
                </button>
              </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px', marginBottom: '20px', position: 'relative' }}>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Origin Station</label>
              <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#3b82f6' }}>
                  <MapPinIcon size={16} />
                </div>
                <input 
                  type="text" 
                  value={fromSearchText || (selectedMeta ? selectedMeta.name : '')} 
                  onKeyDown={(e) => handleMapKeyDown(e, fromSuggestions, activeFromIndex, setActiveFromIndex, ([id, s]) => {
                    setSelectedStationId(id);
                    setFromSearchText('');
                  })}
                  onChange={(e) => {
                    setFromSearchText(e.target.value);
                    setActiveFromIndex(-1);
                    if (selectedStationId) setSelectedStationId(null);
                  }}
                  placeholder="Enter start station..."
                  style={{ 
                    width: '100%',
                    padding: '12px 12px 12px 36px', 
                    borderRadius: '8px', 
                    border: '1px solid #cbd5e1', 
                    backgroundColor: selectedStationId ? '#f8fafc' : 'white',
                    color: '#0f172a',
                    outline: 'none',
                    fontSize: '14px',
                    fontWeight: 500,
                    boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.02)'
                  }} 
                />
              </div>
              {fromSuggestions.length > 0 && !selectedStationId && (
                <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '4px', marginTop: '4px', width: '100%', maxHeight: '200px', overflowY: 'auto' }}>
                  {fromSuggestions.map(([id, s], idx) => (
                    <div 
                      key={id} 
                      onMouseEnter={() => setActiveFromIndex(idx)}
                      onClick={() => { setSelectedStationId(id); setFromSearchText(''); }} 
                      style={{ padding: '8px', cursor: 'pointer', fontSize: '13px', borderBottom: '1px solid #f1f5f9', color: idx === activeFromIndex ? '#2563eb' : '#334155', fontWeight: idx === activeFromIndex ? 'bold' : 'normal', background: idx === activeFromIndex ? '#eff6ff' : 'transparent' }}
                    >
                      {s.name}
                    </div>
                  ))}
                </div>
              )}
            </div>
            
            <button 
              onClick={() => {
                const temp = selectedStationId;
                setSelectedStationId(toStationId);
                setToStationId(temp);
                setFromSearchText('');
                setToSearchText('');
              }}
              style={{
                position: 'absolute',
                top: '50%',
                right: '20px',
                transform: 'translateY(-50%)',
                background: 'white',
                border: '1px solid #cbd5e1',
                borderRadius: '50%',
                width: '32px',
                height: '32px',
                display: 'flex',
                justifyContent: 'center',
                alignItems: 'center',
                cursor: 'pointer',
                boxShadow: '0 2px 4px rgba(0,0,0,0.05)',
                zIndex: 5
              }}
            >
              <ArrowUpDown size={16} color="#64748b" />
            </button>

            <div style={{ display: 'flex', flexDirection: 'column', gap: '4px' }}>
              <label style={{ fontSize: '11px', fontWeight: 700, color: '#64748b', textTransform: 'uppercase', letterSpacing: '0.5px' }}>Destination Station</label>
              <div style={{ position: 'relative' }}>
                <div style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)', color: '#ef4444' }}>
                  <Target size={16} />
                </div>
                <input 
                  type="text" 
                  value={toSearchText || (toStationId ? stationsMeta[toStationId]?.name : '')} 
                  onKeyDown={(e) => handleMapKeyDown(e, toSuggestions, activeToIndex, setActiveToIndex, ([id, s]) => {
                    setToStationId(id);
                    setToSearchText('');
                  })}
                  onChange={(e) => {
                    setToSearchText(e.target.value);
                    setActiveToIndex(-1);
                    if (toStationId) setToStationId(null);
                  }}
                  placeholder="Enter destination..."
                  style={{ 
                    width: '100%',
                    padding: '12px 12px 12px 36px', 
                    borderRadius: '8px', 
                    border: '1px solid #cbd5e1', 
                    backgroundColor: toStationId ? '#f8fafc' : 'white',
                    color: '#0f172a',
                    outline: 'none',
                    fontSize: '14px',
                    fontWeight: 500,
                    boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.02)'
                  }} 
                />
              </div>
              {toSuggestions.length > 0 && !toStationId && (
                <div style={{ background: 'white', border: '1px solid #e2e8f0', borderRadius: '4px', marginTop: '4px', width: '100%', maxHeight: '200px', overflowY: 'auto' }}>
                  {toSuggestions.map(([id, s], idx) => (
                    <div 
                      key={id} 
                      onMouseEnter={() => setActiveToIndex(idx)}
                      onClick={() => { setToStationId(id); setToSearchText(''); }} 
                      style={{ padding: '8px', cursor: 'pointer', fontSize: '13px', borderBottom: '1px solid #f1f5f9', color: idx === activeToIndex ? '#2563eb' : '#334155', fontWeight: idx === activeToIndex ? 'bold' : 'normal', background: idx === activeToIndex ? '#eff6ff' : 'transparent' }}
                    >
                      {s.name}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {toStationId ? (
            <div>
              {routePaths.length === 0 ? (
                <div style={{ fontSize: '13px', color: '#ef4444' }}>No path found between these stations.</div>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
                  {(() => {
                    const path = routePaths[selectedPathIndex] || routePaths[0];
                    const fullTrace = [
                      stationsMeta[selectedStationId as string]?.name || 'Origin',
                      ...path.segments.map((seg: any) => stationsMeta[seg.to]?.name || 'Unknown')
                    ];

                    let displayTrace = fullTrace;
                    if (fullTrace.length > 5) {
                      displayTrace = [
                        fullTrace[0],
                        fullTrace[1],
                        '...',
                        fullTrace[fullTrace.length - 2],
                        fullTrace[fullTrace.length - 1]
                      ];
                    }

                    // Real Timetable Matching!
                    const normalize = (name: string) => {
                      if (!name) return '';
                      return name.toLowerCase().replace(/ junction| jn| cantt| cant| city| cb/g, '').trim();
                    };

                    const originName = stationsMeta[selectedStationId as string]?.name || '';
                    const destName = stationsMeta[toStationId as string]?.name || '';
                    const normOrigin = normalize(originName);
                    const normDest = normalize(destName);

                    const matchedTrains: any[] = [];
                    for (const [tno, t] of Object.entries(timetable)) {
                      const stops = (t as any).s;
                      let oIdx = -1;
                      let dIdx = -1;
                      
                      for (let i = 0; i < stops.length; i++) {
                        const sName = normalize(stops[i][0]);
                        if (sName === normOrigin) oIdx = i;
                        if (sName === normDest) dIdx = i;
                      }
                      
                      if (oIdx !== -1 && dIdx !== -1 && oIdx < dIdx) {
                        // Calculate duration
                        const dep = stops[oIdx][2];
                        const arr = stops[dIdx][1];
                        matchedTrains.push({
                          train_number: tno,
                          train_name: (t as any).n,
                          dep_time: dep,
                          arr_time: arr,
                          dep_station: stops[oIdx][0],
                          arr_station: stops[dIdx][0]
                        });
                      }
                    }

                    // Sort by departure time
                    matchedTrains.sort((a, b) => a.dep_time.localeCompare(b.dep_time));

                    return (
                      <div style={{ 
                        padding: '16px', 
                        border: '1px solid #e2e8f0',
                        borderRadius: '12px',
                        background: 'white',
                        boxShadow: '0 4px 12px rgba(0,0,0,0.05)'
                      }}>
                        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '12px' }}>
                          <h3 style={{ fontSize: '14px', margin: 0, color: '#1e293b', fontWeight: 700 }}>
                            Route Overview
                          </h3>
                          <div style={{ display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <MapPin size={14} color="#3b82f6" />
                            <span style={{ fontWeight: 700, color: '#3b82f6', fontSize: '14px' }}>
                              {Math.round(path.dist)} km
                            </span>
                          </div>
                        </div>
                        
                        <div style={{ 
                          fontSize: '13px', 
                          color: '#64748b', 
                          lineHeight: '1.6', 
                          display: 'flex', 
                          flexWrap: 'wrap', 
                          alignItems: 'center', 
                          gap: '6px',
                          marginBottom: '20px',
                          paddingBottom: '16px',
                          borderBottom: '1px solid #f1f5f9'
                        }}>
                          {displayTrace.map((name, i) => (
                            <React.Fragment key={i}>
                              <span style={{ 
                                color: (i === 0 || i === displayTrace.length - 1) ? '#0f172a' : '#64748b', 
                                fontWeight: (i === 0 || i === displayTrace.length - 1) ? 600 : 400 
                              }}>
                                {name}
                              </span>
                              {i < displayTrace.length - 1 && <span style={{ color: '#cbd5e1', fontSize: '12px', fontWeight: 700 }}>→</span>}
                            </React.Fragment>
                          ))}
                        </div>

                        <div>
                          <h4 style={{ fontSize: '12px', fontWeight: 700, color: '#475569', marginBottom: '12px', textTransform: 'uppercase', letterSpacing: '0.5px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                            <Train size={14} />
                            Available Trains ({matchedTrains.length})
                          </h4>
                          
                          {matchedTrains.length === 0 && (
                            <div style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic' }}>
                              No scheduled trains found connecting these specific stations.
                            </div>
                          )}

                          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px', maxHeight: '400px', overflowY: 'auto', paddingRight: '4px' }}>
                            {matchedTrains.map(t => (
                              <div key={t.train_number} onClick={() => setSelectedTrain({
                                ...t,
                                delayMinutes: Math.floor(Math.random() * 45),
                                currentStationIndex: Math.max(1, Math.floor((timetable[t.train_number]?.s?.length || 2) / 2))
                              })} style={{ display: 'flex', flexDirection: 'column', background: '#f8fafc', padding: '12px', borderRadius: '8px', border: '1px solid #e2e8f0', transition: 'all 0.2s', cursor: 'pointer' }} className="train-card">
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                                  <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
                                    <div style={{ background: '#e0e7ff', color: '#4f46e5', fontWeight: 700, fontSize: '12px', padding: '4px 8px', borderRadius: '6px' }}>
                                      {t.train_number}
                                    </div>
                                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#1e293b' }}>
                                      {t.train_name}
                                    </div>
                                  </div>
                                </div>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '4px' }}>
                                  <div style={{ display: 'flex', flexDirection: 'column' }}>
                                    <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>{t.dep_time.substring(0, 5)}</div>
                                    <div style={{ fontSize: '11px', color: '#64748b' }}>{t.dep_station}</div>
                                  </div>
                                  
                                  <div style={{ flex: 1, borderTop: '2px dashed #cbd5e1', margin: '0 12px', position: 'relative', top: '-6px' }}></div>
                                  
                                  <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'flex-end' }}>
                                    <div style={{ fontSize: '15px', fontWeight: 700, color: '#0f172a' }}>{t.arr_time.substring(0, 5)}</div>
                                    <div style={{ fontSize: '11px', color: '#64748b' }}>{t.arr_station}</div>
                                  </div>
                                </div>
                              </div>
                            ))}
                          </div>
                        </div>
                      </div>
                    );
                  })()}
                </div>
              )}
            </div>
          ) : (
            <div>
              <h3 style={{ fontSize: '14px', margin: '0 0 12px 0', color: '#475569', borderBottom: '1px solid #e2e8f0', paddingBottom: '8px', display: 'flex', alignItems: 'center', gap: '8px' }}>
                <Train size={16} color="#64748b" />
                Direct Connections ({connectedBranches.length})
              </h3>

              <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
                {connectedBranches.map((branch: any) => {
                  const mainId = branch.mainStationId;
                  const mainMeta = stationsMeta[mainId] || { name: 'Unknown Main Station' };
                  const isExpanded = expandedMainId === mainId;

                  // Get connected middles strictly on this path
                  const mainMiddles = isExpanded 
                ? (branch.middleStationIds || [])
                  .map((id: string) => ({ id, ...stationsMeta[id] }))
                : [];

              return (
                <div key={mainId} style={{
                  border: isExpanded ? '1px solid #93c5fd' : '1px solid #e2e8f0',
                  borderRadius: '8px',
                  overflow: 'hidden',
                  background: isExpanded ? '#f8fafc' : 'white',
                  transition: 'all 0.2s',
                  boxShadow: isExpanded ? '0 2px 8px rgba(59, 130, 246, 0.1)' : '0 1px 2px rgba(0,0,0,0.02)'
                }}>
                  <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 14px' }}>
                    <div 
                      onClick={() => setToStationId(mainId)}
                      style={{ flex: 1, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '10px' }}
                    >
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#3b82f6' }}></div>
                      <span style={{ fontWeight: 600, fontSize: '14px', color: '#1e293b' }}>
                        {mainMeta.name}
                      </span>
                    </div>
                    
                    <button
                      onClick={(e) => {
                        e.stopPropagation();
                        setExpandedMainId(isExpanded ? null : mainId);
                      }}
                      style={{
                        background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8',
                        display: 'flex', alignItems: 'center', justifyContent: 'center', padding: '4px'
                      }}
                    >
                      {isExpanded ? <ChevronUp size={16} /> : <ChevronDown size={16} />}
                    </button>
                  </div>

                  {isExpanded && (
                    <div style={{ padding: '0 14px 14px 14px' }}>
                      <div style={{ height: '1px', background: '#e2e8f0', margin: '0 0 10px 0' }}></div>
                      <div style={{ fontSize: '11px', color: '#64748b', fontWeight: 700, textTransform: 'uppercase', marginBottom: '8px', letterSpacing: '0.5px' }}>
                        Stops Along The Way ({mainMiddles.length})
                      </div>
                      {mainMiddles.length > 0 ? (
                        <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                          {mainMiddles.map((mid: any) => (
                            <div 
                              key={mid.id}
                              onClick={() => setToStationId(mid.id)}
                              style={{
                                padding: '8px 12px',
                                background: 'white',
                                border: '1px solid #e2e8f0',
                                borderRadius: '6px',
                                fontSize: '13px',
                                color: '#475569',
                                cursor: 'pointer',
                                transition: 'background 0.2s',
                                display: 'flex',
                                alignItems: 'center',
                                gap: '8px'
                              }}
                              onMouseOver={(e) => e.currentTarget.style.background = '#f1f5f9'}
                              onMouseOut={(e) => e.currentTarget.style.background = 'white'}
                            >
                              <div style={{ width: '4px', height: '4px', borderRadius: '50%', background: '#cbd5e1' }}></div>
                              {mid.name}
                            </div>
                          ))}
                        </div>
                      ) : (
                        <div style={{ fontSize: '12px', color: '#94a3b8', fontStyle: 'italic' }}>
                          No middle stations on this path.
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}

            {connectedBranches.length === 0 && (
              <div style={{ fontSize: '13px', color: '#64748b', fontStyle: 'italic' }}>
                No connected stations found.
              </div>
            )}
            </div>
            </div>
          )}
          </>
        )}
      </div>
    )}

      {/* Right Sidebar for Live Trains */}
      {isRightSidebarOpen && (
        <div style={{
          position: 'absolute',
          right: 0,
          top: 0,
          bottom: 0,
          width: '380px',
          backgroundColor: 'rgba(255, 255, 255, 0.95)',
          backdropFilter: 'blur(8px)',
          boxShadow: '-4px 0 25px rgba(0,0,0,0.1)',
          padding: '24px',
          overflowY: 'auto',
          display: 'flex',
          flexDirection: 'column',
          zIndex: 50,
          borderLeft: '1px solid rgba(0,0,0,0.05)',
          color: '#1e293b'
        }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
            <h2 style={{ margin: 0, fontSize: '20px', fontWeight: 700, display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Radio size={20} color="#ef4444" /> Live Running Trains
            </h2>
            <button 
              onClick={() => setIsRightSidebarOpen(false)}
              style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#94a3b8' }}
            >
              <X size={20} />
            </button>
          </div>

          <div style={{ position: 'relative', marginBottom: '16px', flexShrink: 0 }}>
             <Search size={16} color="#64748b" style={{ position: 'absolute', left: '12px', top: '50%', transform: 'translateY(-50%)' }} />
             <input 
               type="text"
               placeholder="Search by name or number..."
               value={liveTrainSearchText}
               onChange={(e) => setLiveTrainSearchText(e.target.value)}
               style={{
                 width: '100%',
                 padding: '10px 10px 10px 36px',
                 borderRadius: '8px',
                 border: '1px solid #cbd5e1',
                 outline: 'none',
                 fontSize: '13px',
                 color: '#0f172a',
                 boxShadow: 'inset 0 1px 2px rgba(0,0,0,0.02)'
               }}
             />
          </div>

          <div style={{ display: 'flex', gap: '8px', overflowX: 'auto', marginBottom: '16px', paddingBottom: '4px', scrollbarWidth: 'none', flexShrink: 0 }}>
            {['All', 'Northern', 'Southern', 'Eastern', 'Western', 'Central'].map(zone => (
              <button
                key={zone}
                onClick={() => { setVisibleTrainsCount(15); setSelectedZone(zone); }}
                style={{
                  padding: '6px 12px',
                  borderRadius: '16px',
                  border: 'none',
                  fontSize: '12px',
                  fontWeight: 600,
                  whiteSpace: 'nowrap',
                  cursor: 'pointer',
                  background: selectedZone === zone ? '#3b82f6' : '#f1f5f9',
                  color: selectedZone === zone ? '#ffffff' : '#475569',
                  transition: 'all 0.2s',
                  flexShrink: 0
                }}
              >
                {zone}
              </button>
            ))}
          </div>

          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            {(() => {
              const allFilteredTrains = memoizedMockTrains.filter((t: any) => {
                const matchesSearch = (t.id && t.id.toLowerCase().includes(liveTrainSearchText.toLowerCase())) || 
                                      (t.name && t.name.toLowerCase().includes(liveTrainSearchText.toLowerCase()));
                const matchesZone = selectedZone === 'All' || t.zone === selectedZone;
                return matchesSearch && matchesZone;
              });
                
              const displayTrains = allFilteredTrains.slice(0, visibleTrainsCount);

              if (allFilteredTrains.length === 0) {
                return (
                  <div style={{ textAlign: 'center', padding: '40px 20px', color: '#94a3b8' }}>
                    <Train size={48} style={{ margin: '0 auto 16px auto', opacity: 0.5 }} />
                    <p>No running trains match your search.</p>
                  </div>
                );
              }

              const trainCards = displayTrains.map((train: any) => (
                <div 
                  key={train.id}
                  onClick={() => {
                    if (timetable[train.id]) {
                      setSelectedTrain({
                        ...timetable[train.id],
                        train_number: train.id,
                        train_name: train.name,
                        dep_station: timetable[train.id].s[0][0],
                        arr_station: timetable[train.id].s[timetable[train.id].s.length - 1][0],
                        delayMinutes: train.delayMin,
                        currentStationIndex: Math.max(1, Math.floor((timetable[train.id]?.s?.length || 2) / 2))
                      });
                      setIsSidebarOpen(true);
                      
                      // Focus map if location is available
                      if (Array.isArray(train.currentLocation) && train.currentLocation.length === 2 && mapRef.current) {
                        mapRef.current.flyTo({ center: train.currentLocation as [number, number], zoom: 11, duration: 1500 });
                      }
                    }
                  }}
                  style={{
                    background: 'white',
                    border: '1px solid #e2e8f0',
                    borderRadius: '10px',
                    padding: '12px 14px',
                    cursor: 'pointer',
                    boxShadow: '0 1px 3px rgba(0,0,0,0.02)',
                    transition: 'all 0.2s'
                  }}
                  onMouseEnter={(e) => {
                    e.currentTarget.style.borderColor = '#93c5fd';
                    e.currentTarget.style.boxShadow = '0 4px 12px rgba(59, 130, 246, 0.1)';
                  }}
                  onMouseLeave={(e) => {
                    e.currentTarget.style.borderColor = '#e2e8f0';
                    e.currentTarget.style.boxShadow = '0 1px 3px rgba(0,0,0,0.02)';
                  }}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '8px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ background: '#e0e7ff', color: '#4f46e5', fontWeight: 700, fontSize: '11px', padding: '3px 6px', borderRadius: '4px' }}>
                        {train.id}
                      </div>
                      {train.zone && (
                        <div style={{ background: '#f1f5f9', color: '#64748b', fontWeight: 600, fontSize: '9px', padding: '2px 4px', borderRadius: '4px', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
                          {train.zone}
                        </div>
                      )}
                      <div style={{ fontSize: '13px', fontWeight: 700, color: '#0f172a', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis', maxWidth: '100px' }} title={train.name}>
                        {train.name}
                      </div>
                    </div>
                    <div style={{ 
                      background: train.delayMin > 20 ? '#fee2e2' : (train.delayMin > 0 ? '#fef3c7' : '#dcfce7'), 
                      color: train.delayMin > 20 ? '#ef4444' : (train.delayMin > 0 ? '#d97706' : '#15803d'), 
                      padding: '2px 6px', borderRadius: '8px', fontSize: '10px', fontWeight: 800,
                      whiteSpace: 'nowrap'
                    }}>
                      {train.delayMin > 0 ? `+${train.delayMin}m` : 'ON TIME'}
                    </div>
                  </div>
                  
                  <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '11px', color: '#64748b', marginBottom: '6px' }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px' }}>
                      <Clock size={11} /> Sched: {train.scheduledEta}
                    </div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#2563eb', fontWeight: 600 }}>
                      <Target size={11} /> AI: {train.aiEta}
                    </div>
                  </div>
                  
                  <div style={{ fontSize: '11px', color: '#475569', display: 'flex', alignItems: 'center', gap: '6px' }}>
                    <div style={{ width: '5px', height: '5px', borderRadius: '50%', background: '#10b981', animation: 'pulse 2s infinite' }}></div>
                    Currently near: <span style={{ fontWeight: 600 }}>{train.currentLocationName || (typeof train.currentLocation === 'string' ? train.currentLocation : 'Live Track')}</span>
                  </div>
                  
                  <div style={{ marginTop: '8px', borderTop: '1px dashed #cbd5e1', paddingTop: '8px', fontSize: '11px', color: '#64748b', display: 'flex', justifyContent: 'space-between' }}>
                    <span>Speed: <strong>{train.currentSpeed?.toFixed(0) || 0} km/h</strong></span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#10b981' }}>
                      <CheckCircle2 size={11} /> AI Conf: {train.confidence || 95}%
                    </span>
                  </div>
                </div>
              ));

              return (
                <>
                  {trainCards}
                  {allFilteredTrains.length > visibleTrainsCount && (
                    <button
                      onClick={() => setVisibleTrainsCount(prev => prev + 15)}
                      style={{
                        padding: '10px',
                        background: '#f1f5f9',
                        border: 'none',
                        borderRadius: '8px',
                        color: '#475569',
                        fontWeight: 600,
                        cursor: 'pointer',
                        marginTop: '4px',
                        transition: 'background 0.2s',
                        display: 'flex',
                        justifyContent: 'center',
                        alignItems: 'center',
                        gap: '6px'
                      }}
                      onMouseEnter={(e) => e.currentTarget.style.background = '#e2e8f0'}
                      onMouseLeave={(e) => e.currentTarget.style.background = '#f1f5f9'}
                    >
                      <Plus size={16} /> See More Trains
                    </button>
                  )}
                </>
              );
            })()}
          </div>
        </div>
      )}

      {/* Tooltip Hover Overlay */}
      {hoverInfo && (
        <div style={{
          position: 'absolute',
          left: hoverInfo.x,
          top: hoverInfo.y,
          background: 'rgba(255, 255, 255, 0.95)', // White Theme
          border: '1px solid rgba(0, 0, 0, 0.1)',
          boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1)',
          color: '#1e293b', // Slate 800
          padding: '10px 14px',
          borderRadius: '8px',
          pointerEvents: 'none',
          transform: 'translate(-50%, -100%)',
          marginTop: '-15px',
          zIndex: 100,
          whiteSpace: 'nowrap',
          backdropFilter: 'blur(4px)'
        }}>
          <div style={{ fontWeight: 'bold', fontSize: '14px', marginBottom: '4px' }}>
            {hoverInfo.feature.properties.name || 'Unknown Station'}
          </div>
          <div style={{
            fontSize: '11px',
            fontWeight: 600,
            textTransform: 'uppercase',
            letterSpacing: '0.05em',
            color: hoverInfo.feature.properties.stationClass === 'main' ? '#d97706' : '#64748b' // Amber 600 for main, Slate 500 for middle
          }}>
            {/* {hoverInfo.feature.properties.stationClass === 'main' ? '⭐ Main Station' : 'Intermediate Stop'} */}
          </div>
          <div style={{ fontSize: '10px', color: '#94a3b8', marginTop: '4px' }}>
            ID: {hoverInfo.feature.properties.stationId}
          </div>
        </div>
      )}

      {/* AI Analysis Modal */}
      {showAiModal && selectedTrain && (
        <div style={{
          position: 'fixed',
          top: 0, left: 0, right: 0, bottom: 0,
          backgroundColor: 'rgba(15, 23, 42, 0.4)',
          backdropFilter: 'blur(4px)',
          zIndex: 9999,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '40px'
        }}>
          <div style={{
            background: '#ffffff',
            borderRadius: '16px',
            width: '100%',
            maxWidth: '1000px',
            maxHeight: '90vh',
            display: 'flex',
            flexDirection: 'column',
            boxShadow: '0 25px 50px -12px rgba(0, 0, 0, 0.25)',
            overflow: 'hidden'
          }}>
            {/* Modal Header */}
            <div style={{ padding: '20px 24px', borderBottom: '1px solid #e2e8f0', display: 'flex', alignItems: 'center', justifyContent: 'space-between', backgroundColor: '#f8fafc' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
                <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: '#eff6ff', color: '#3b82f6', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
                  <Train size={24} />
                </div>
                <div>
                  <h2 style={{ margin: 0, fontSize: '18px', fontWeight: 700, color: '#0f172a' }}>
                    Route Details: {selectedTrain.dep_station} -{'>'} {selectedTrain.arr_station}
                  </h2>
                  <div style={{ fontSize: '13px', color: '#64748b', marginTop: '2px', fontWeight: 400 }}>
                    Live 30-Second Closed-Loop Telemetry & AI Prediction Stream
                  </div>
                </div>
              </div>
              <button onClick={() => setShowAiModal(false)} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748b' }}>
                <X size={24} />
              </button>
            </div>

            {/* Modal Content */}
            <div style={{ padding: '24px', overflowY: 'auto', flex: 1 }}>
              
              {/* Train Status Card */}
              <div style={{ border: '1px solid #e2e8f0', borderRadius: '12px', padding: '20px', marginBottom: '24px', backgroundColor: '#ffffff' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                  <div>
                    <h3 style={{ margin: '0 0 4px 0', fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>
                      {selectedTrain.train_number} - {selectedTrain.train_name}
                    </h3>
                    <div style={{ fontSize: '13px', color: '#64748b', display: 'flex', alignItems: 'center', gap: '8px' }}>
                      <div style={{ width: '8px', height: '8px', borderRadius: '50%', background: '#60a5fa' }}></div>
                      Currently at: <span style={{ fontWeight: 600, color: '#334155' }}>{timetable[selectedTrain.train_number]?.s[selectedTrain.currentStationIndex]?.[0]}</span>
                    </div>
                  </div>
                  <div style={{ background: '#fee2e2', color: '#ef4444', padding: '4px 12px', borderRadius: '20px', fontSize: '12px', fontWeight: 800, letterSpacing: '0.05em' }}>
                    {selectedTrain.delayMinutes > 20 ? 'CRITICAL' : (selectedTrain.delayMinutes > 0 ? 'DELAYED' : 'ON TIME')}
                  </div>
                </div>

                {/* 4-Col Metrics */}
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '16px', borderTop: '1px solid #f1f5f9', paddingTop: '16px' }}>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>Scheduled ETA</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: '#0f172a' }}>{timetable[selectedTrain.train_number]?.s[timetable[selectedTrain.train_number]?.s.length - 1]?.[1] || 'N/A'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#3b82f6', textTransform: 'uppercase', marginBottom: '4px' }}>AI Predicted ETA</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: '#2563eb' }}>{timetable[selectedTrain.train_number]?.s[timetable[selectedTrain.train_number]?.s.length - 1]?.[1] || 'N/A'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>Dynamic Delay</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: selectedTrain.delayMinutes > 0 ? '#ef4444' : '#10b981' }}>{selectedTrain.delayMinutes > 0 ? `+${selectedTrain.delayMinutes} min` : 'ON TIME'}</div>
                  </div>
                  <div>
                    <div style={{ fontSize: '11px', fontWeight: 700, color: '#94a3b8', textTransform: 'uppercase', marginBottom: '4px' }}>AI Confidence</div>
                    <div style={{ fontSize: '16px', fontWeight: 700, color: '#10b981' }}>94%</div>
                  </div>
                </div>
              </div>

              {/* Delay Alert (Conditional) */}
              {selectedTrain.delayMinutes > 0 && (
                <div style={{ background: '#fee2e2', border: '1px solid #fca5a5', borderRadius: '8px', padding: '16px', marginBottom: '16px', display: 'flex', gap: '12px' }}>
                  <AlertTriangle size={20} color="#ef4444" style={{ marginTop: '2px' }} />
                  <div>
                    <div style={{ fontSize: '13px', fontWeight: 700, color: '#ef4444', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Delay Factor Identified</div>
                    <div style={{ fontSize: '14px', color: '#b91c1c', marginTop: '4px' }}>Monsoon Heavy Downpour & Shivalik Foothill Caution (Cap: 45.0 km/h)</div>
                  </div>
                </div>
              )}

              {/* View Context Button */}
            

              {/* Table Header Section */}
              <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '16px' }}>
                <Activity size={18} color="#3b82f6" />
                <h3 style={{ margin: 0, fontSize: '13px', fontWeight: 700, color: '#1e293b', textTransform: 'uppercase', letterSpacing: '0.05em' }}>Station-Wise Prediction & Timetable Analysis</h3>
              </div>

              {/* Table */}
              <div style={{ border: '1px solid #e2e8f0', borderRadius: '12px', overflow: 'hidden' }}>
                <table style={{ width: '100%', borderCollapse: 'collapse', textAlign: 'left' }}>
                  <thead>
                    <tr style={{ background: '#f8fafc', borderBottom: '1px solid #e2e8f0' }}>
                      <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 600, color: '#64748b' }}>STATION</th>
                      <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 600, color: '#64748b' }}>SCHEDULED</th>
                      <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 600, color: '#64748b' }}>AI PREDICTED</th>
                      <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 600, color: '#64748b' }}>DELAY</th>
                      <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 600, color: '#64748b' }}>CONFIDENCE</th>
                      <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 600, color: '#64748b' }}>FACTOR</th>
                      <th style={{ padding: '12px 16px', fontSize: '11px', fontWeight: 600, color: '#64748b', textAlign: 'right' }}>DESTINATION ETA</th>
                    </tr>
                  </thead>
                  <tbody>
                    {timetable[selectedTrain.train_number]?.s.map((stop: any, idx: number) => {
                       // Only show upcoming stations (or all for demo, let's just show all)
                       const isPast = idx < selectedTrain.currentStationIndex;
                       return (
                         <tr key={idx} style={{ borderBottom: '1px solid #f1f5f9', opacity: isPast ? 0.6 : 1 }}>
                           <td style={{ padding: '12px 16px' }}>
                             <div style={{ fontWeight: 600, color: '#0f172a', fontSize: '14px' }}>{stop[0]}</div>
                             <div style={{ fontSize: '12px', color: '#94a3b8', marginTop: '2px' }}>{stop[0].substring(0, 4).toUpperCase()}</div>
                           </td>
                           <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 500, color: '#334155' }}>{stop[1]}</td>
                           <td style={{ padding: '12px 16px', fontSize: '14px', fontWeight: 600, color: '#2563eb' }}>{stop[1]}</td>
                           <td style={{ padding: '12px 16px' }}>
                             {selectedTrain.delayMinutes > 0 ? (
                               <div style={{ background: '#fee2e2', color: '#ef4444', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 700, display: 'inline-block' }}>+{selectedTrain.delayMinutes}m</div>
                             ) : (
                               <div style={{ color: '#10b981', fontSize: '12px', fontWeight: 700 }}>--</div>
                             )}
                           </td>
                           <td style={{ padding: '12px 16px' }}>
                             <div style={{ display: 'flex', alignItems: 'center', gap: '4px', color: '#10b981', fontSize: '14px', fontWeight: 500 }}>
                               <CheckCircle2 size={14} /> 94%
                             </div>
                           </td>
                           <td style={{ padding: '12px 16px', fontSize: '13px', color: selectedTrain.delayMinutes > 0 ? '#ef4444' : '#64748b', display: 'flex', alignItems: 'center', gap: '6px' }}>
                             {selectedTrain.delayMinutes > 0 && <AlertTriangle size={12} />} 
                             {selectedTrain.delayMinutes > 0 ? 'Monsoon Heavy Downpour & Shivali...' : 'Clear Track'}
                           </td>
                           <td style={{ padding: '12px 16px', textAlign: 'right', fontWeight: 700, color: '#1e40af', fontSize: '14px' }}>
                             {timetable[selectedTrain.train_number]?.s[timetable[selectedTrain.train_number]?.s.length - 1]?.[1] || 'N/A'}
                           </td>
                         </tr>
                       );
                    })}
                  </tbody>
                </table>
              </div>

            </div>
          </div>
        </div>
      )}
    </div>
  );
};
