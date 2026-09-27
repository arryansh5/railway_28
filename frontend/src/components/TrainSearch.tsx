import React, { useState, useEffect, useMemo, useRef } from 'react';
import { ArrowRight, Train, ArrowUpDown } from 'lucide-react';
import { useNavigate } from 'react-router-dom';

export const TrainSearch: React.FC = () => {
  const navigate = useNavigate();
  const [fromStation, setFromStation] = useState('');
  const [toStation, setToStation] = useState('');
  const [trainNumber, setTrainNumber] = useState('');
  const [stationsMeta, setStationsMeta] = useState<Record<string, any>>({});
  const [timetable, setTimetable] = useState<Record<string, any>>({});
  const [showFromDropdown, setShowFromDropdown] = useState(false);
  const [showToDropdown, setShowToDropdown] = useState(false);
  const [showTrainDropdown, setShowTrainDropdown] = useState(false);
  
  const [activeFromIndex, setActiveFromIndex] = useState(-1);
  const [activeToIndex, setActiveToIndex] = useState(-1);
  const [activeTrainIndex, setActiveTrainIndex] = useState(-1);
  
  const fromRef = useRef<HTMLDivElement>(null);
  const toRef = useRef<HTMLDivElement>(null);
  const trainRef = useRef<HTMLDivElement>(null);
  useEffect(() => {
    fetch('/stations_metadata.json')
      .then(res => res.json())
      .then(data => setStationsMeta(data))
      .catch(console.error);
      
    fetch('/timetable.json')
      .then(res => res.json())
      .then(data => setTimetable(data))
      .catch(console.error);
  }, []);

  const trainSuggestions = useMemo(() => {
    if (!trainNumber || trainNumber.length < 2) return [];
    const lower = trainNumber.toLowerCase();
    return Object.entries(timetable)
      .filter(([id, data]: [string, any]) => 
        id.includes(lower) || data.n.toLowerCase().includes(lower)
      )
      .map(([id, data]: [string, any]) => ({ id, name: data.n }))
      .slice(0, 50);
  }, [trainNumber, timetable]);
  
  const fromSuggestions = useMemo(() => {
    if (!fromStation || fromStation.length < 2) return [];
    const lower = fromStation.toLowerCase();
    return Object.values(stationsMeta)
      .filter((s: any) => s.name.toLowerCase().includes(lower))
      .slice(0, 50);
  }, [fromStation, stationsMeta]);

  const toSuggestions = useMemo(() => {
    if (!toStation || toStation.length < 2) return [];
    const lower = toStation.toLowerCase();
    return Object.values(stationsMeta)
      .filter((s: any) => s.name.toLowerCase().includes(lower))
      .slice(0, 50);
  }, [toStation, stationsMeta]);

  const handleKeyDown = (
    e: React.KeyboardEvent,
    suggestions: any[],
    activeIndex: number,
    setActiveIndex: React.Dispatch<React.SetStateAction<number>>,
    setSelection: (val: string) => void,
    closeDropdown: () => void,
    isTrain: boolean,
    listRef: React.RefObject<HTMLDivElement>
  ) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault();
      setActiveIndex(prev => {
        const next = prev < suggestions.length - 1 ? prev + 1 : prev;
        scrollToActive(listRef, next);
        return next;
      });
    } else if (e.key === 'ArrowUp') {
      e.preventDefault();
      setActiveIndex(prev => {
        const next = prev > 0 ? prev - 1 : 0;
        scrollToActive(listRef, next);
        return next;
      });
    } else if (e.key === 'Enter') {
      e.preventDefault();
      if (activeIndex >= 0 && activeIndex < suggestions.length) {
        const selected = suggestions[activeIndex];
        setSelection(isTrain ? `${selected.id} - ${selected.name}` : selected.name);
        closeDropdown();
        setActiveIndex(-1);
      } else {
        if (isTrain) handleLiveStatus();
        else handleFindTrains();
      }
    }
  };

  const scrollToActive = (ref: React.RefObject<HTMLDivElement>, index: number) => {
    if (ref.current) {
      const activeEl = ref.current.children[index] as HTMLElement;
      if (activeEl) {
        activeEl.scrollIntoView({ block: 'nearest' });
      }
    }
  };

  const handleSwap = () => {
    const temp = fromStation;
    setFromStation(toStation);
    setToStation(temp);
  };

  const handleFindTrains = () => {
    navigate(`/map?from=${encodeURIComponent(fromStation)}&to=${encodeURIComponent(toStation)}`);
  };

  const handleLiveStatus = () => {
    if (trainNumber.trim()) {
      const match = trainNumber.match(/^(\d+)/);
      const id = match ? match[1] : trainNumber.trim();
      navigate(`/map?train=${encodeURIComponent(id)}`);
    }
  };

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 font-sans w-full items-start">
      {/* Find Trains Card */}
      <div className="bg-background border border-border rounded-xl shadow-sm">
        {/* Header */}
        <div className="px-5 py-4 flex items-center gap-3 border-b border-border bg-surface/50">
          <div className="bg-primary/10 p-2 rounded-lg flex items-center justify-center border border-primary/20">
            <ArrowRight className="w-4 h-4 text-primary" />
          </div>
          <h2 className="text-text font-bold text-sm uppercase tracking-wider">Find Trains</h2>
        </div>

        {/* Body */}
        <div className="p-6 relative">
          <div className="flex flex-col gap-5 relative pr-14">
            {/* Connecting Line */}
            <div className="absolute left-[11px] top-[24px] bottom-[24px] w-[2px] bg-border z-0"></div>

            {/* From Station */}
            <div className="flex items-center gap-4 relative z-20">
              <div className="w-[24px] h-[24px] rounded-full border-[3px] border-success bg-background flex-shrink-0"></div>
              <div className="w-full relative">
                <input 
                  type="text" 
                  placeholder="From Station" 
                  value={fromStation}
                  onFocus={() => setShowFromDropdown(true)}
                  onBlur={() => setTimeout(() => { setShowFromDropdown(false); setActiveFromIndex(-1); }, 200)}
                  onKeyDown={(e) => handleKeyDown(e, fromSuggestions, activeFromIndex, setActiveFromIndex, setFromStation, () => setShowFromDropdown(false), false, fromRef)}
                  onChange={(e) => {
                    setFromStation(e.target.value);
                    setShowFromDropdown(true);
                    setActiveFromIndex(-1);
                  }}
                  className="w-full bg-transparent text-text placeholder-textMuted font-medium text-sm focus:outline-none py-1"
                />
                {showFromDropdown && fromSuggestions.length > 0 && (
                  <div ref={fromRef} className="absolute top-full left-0 w-full mt-2 bg-white border border-border rounded-lg shadow-lg overflow-y-auto max-h-60 z-50">
                    {fromSuggestions.map((s: any, idx) => (
                      <div 
                        key={idx}
                        onMouseDown={(e) => {
                          e.preventDefault();
                          setFromStation(s.name);
                          setShowFromDropdown(false);
                          setActiveFromIndex(-1);
                        }}
                        className={`px-4 py-3 cursor-pointer text-sm border-b border-slate-100 last:border-0 ${idx === activeFromIndex ? 'bg-primary/10 text-primary font-bold' : 'hover:bg-slate-50 text-slate-700'}`}
                      >
                        {s.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            {/* Divider */}
            <div className="h-[1px] w-full bg-border absolute top-1/2 left-0 -translate-y-1/2 z-0"></div>

            {/* To Station */}
            <div className="flex items-center gap-4 relative z-10">
              <div className="w-[24px] h-[24px] rounded-full border-[3px] border-primary bg-background flex-shrink-0"></div>
              <div className="w-full relative">
                <input 
                  type="text" 
                  placeholder="To Station" 
                  value={toStation}
                  onFocus={() => setShowToDropdown(true)}
                  onBlur={() => setTimeout(() => { setShowToDropdown(false); setActiveToIndex(-1); }, 200)}
                  onKeyDown={(e) => handleKeyDown(e, toSuggestions, activeToIndex, setActiveToIndex, setToStation, () => setShowToDropdown(false), false, toRef)}
                  onChange={(e) => {
                    setToStation(e.target.value);
                    setShowToDropdown(true);
                    setActiveToIndex(-1);
                  }}
                  className="w-full bg-transparent text-text placeholder-textMuted font-medium text-sm focus:outline-none py-1"
                />
                {showToDropdown && toSuggestions.length > 0 && (
                  <div ref={toRef} className="absolute top-full left-0 w-full mt-2 bg-white border border-border rounded-lg shadow-lg overflow-y-auto max-h-60 z-50">
                    {toSuggestions.map((s: any, idx) => (
                      <div 
                        key={idx}
                        onMouseDown={(e) => {
                          e.preventDefault();
                          setToStation(s.name);
                          setShowToDropdown(false);
                          setActiveToIndex(-1);
                        }}
                        className={`px-4 py-3 cursor-pointer text-sm border-b border-slate-100 last:border-0 ${idx === activeToIndex ? 'bg-primary/10 text-primary font-bold' : 'hover:bg-slate-50 text-slate-700'}`}
                      >
                        {s.name}
                      </div>
                    ))}
                  </div>
                )}
              </div>
            </div>
            
            {/* Swap Button */}
            <button 
              onClick={handleSwap}
              className="absolute right-0 top-1/2 -translate-y-1/2 p-2.5 bg-surface hover:bg-border/50 text-textMuted hover:text-text rounded-full border border-border transition-colors z-10 shadow-sm"
              title="Swap stations"
            >
              <ArrowUpDown className="w-4 h-4" />
            </button>
          </div>

          <button 
            onClick={handleFindTrains}
            className="w-full mt-8 bg-primary hover:bg-primaryHover text-white font-bold py-3.5 rounded-lg flex items-center justify-center gap-2 transition-colors shadow-sm"
          >
            Continue to Map <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>

      {/* Live Train Status Card */}
      <div className="bg-background border border-border rounded-xl shadow-sm">
        {/* Header */}
        <div className="px-5 py-4 flex items-center gap-3 border-b border-border bg-surface/50">
          <div className="bg-primary/10 p-2 rounded-lg flex items-center justify-center border border-primary/20">
            <Train className="w-4 h-4 text-primary" />
          </div>
          <h2 className="text-text font-bold text-sm uppercase tracking-wider">Live Train Status</h2>
        </div>

        {/* Body */}
        <div className="p-6 h-[calc(100%-61px)] flex flex-col">
          <div className="relative">
            <input 
              type="text" 
              placeholder="Enter train number or name..." 
              value={trainNumber}
              onFocus={() => setShowTrainDropdown(true)}
              onBlur={() => setTimeout(() => { setShowTrainDropdown(false); setActiveTrainIndex(-1); }, 200)}
              onKeyDown={(e) => handleKeyDown(e, trainSuggestions, activeTrainIndex, setActiveTrainIndex, setTrainNumber, () => setShowTrainDropdown(false), true, trainRef)}
              onChange={(e) => {
                setTrainNumber(e.target.value);
                setShowTrainDropdown(true);
                setActiveTrainIndex(-1);
              }}
              className="w-full bg-surface border border-border rounded-lg px-4 py-3.5 text-sm text-text placeholder-textMuted font-medium focus:outline-none focus:border-primary/50 transition-colors shadow-inner"
            />
            {showTrainDropdown && trainSuggestions.length > 0 && (
              <div ref={trainRef} className="absolute top-full left-0 w-full mt-2 bg-white border border-border rounded-lg shadow-lg overflow-y-auto max-h-60 z-50">
                {trainSuggestions.map((t: any, idx) => (
                  <div 
                    key={idx}
                    onMouseDown={(e) => {
                      e.preventDefault();
                      setTrainNumber(`${t.id} - ${t.name}`);
                      setShowTrainDropdown(false);
                      setActiveTrainIndex(-1);
                    }}
                    className={`px-4 py-3 cursor-pointer text-sm border-b border-slate-100 last:border-0 ${idx === activeTrainIndex ? 'bg-primary/10 text-primary font-bold' : 'hover:bg-slate-50 text-slate-700'}`}
                  >
                    <span className="font-bold mr-2">{t.id}</span>
                    <span>{t.name}</span>
                  </div>
                ))}
              </div>
            )}
          </div>
          
          <div className="flex-1"></div>

          <button 
            onClick={handleLiveStatus}
            className="w-full mt-8 bg-primary hover:bg-primaryHover text-white font-bold py-3.5 rounded-lg flex items-center justify-center gap-2 transition-colors shadow-sm"
          >
            Continue to Map <ArrowRight className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
};
