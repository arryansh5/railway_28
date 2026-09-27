import re

with open('src/pages/MapPage/Map.tsx', 'r', encoding='utf-8') as f:
    content = f.read()

start_marker = r"<div style={{ display: 'flex', flexDirection: 'column', height: '100%' }}>"
end_marker = r"          ) : ("
start_idx = content.find(start_marker)
end_idx = content.find(end_marker, start_idx)

new_sidebar = '''<div style={{ display: 'flex', flexDirection: 'column', height: '100%', position: 'relative' }}>
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
              </div>
              
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '12px 24px', backgroundColor: '#f8fafc', borderBottom: '1px solid #e2e8f0', fontSize: '11px', fontWeight: 800, color: '#94a3b8', textTransform: 'uppercase' }}>
                <div style={{ width: '60px', textAlign: 'right' }}>ARRIVAL</div>
                <div style={{ backgroundColor: '#f1f5f9', padding: '4px 12px', borderRadius: '12px', color: '#475569', border: '1px solid #e2e8f0' }}>DAY 1 • {new Date().toLocaleDateString('en-US', {day:'numeric', month:'short'}).toUpperCase()}</div>
                <div style={{ flex: 1, textAlign: 'right' }}>DEPARTURE</div>
              </div>
              
              <div style={{ paddingLeft: '24px', paddingRight: '24px', paddingTop: '24px', paddingBottom: '200px', overflowY: 'auto', flex: 1, backgroundColor: '#ffffff' }}>
                <div style={{ position: 'relative', display: 'flex', flexDirection: 'column', gap: '24px' }}>
                  {/* The Track */}
                  <div style={{ 
                    position: 'absolute', 
                    left: '68px', // 60px time col + 8px gap
                    top: '10px', 
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
                    <div id={`train-station-${stop[0]}`} key={idx} style={{ display: 'flex', alignItems: 'center', position: 'relative', zIndex: 2 }}>
                      
                      {/* Left: Time */}
                      <div style={{ width: '60px', textAlign: 'right', display: 'flex', flexDirection: 'column', justifyContent: 'center' }}>
                         <div style={{ fontSize: '13px', fontWeight: 600, color: '#334155' }}>
                            {arrTime}
                         </div>
                         {(isDelayed || isEarly) && (
                            <div style={{ fontSize: '12px', fontWeight: 600, color: displayColor }}>
                              {arrTimeLive}
                            </div>
                         )}
                      </div>

                      {/* Middle: Dot / Train Icon */}
                      <div style={{ width: '32px', display: 'flex', justifyContent: 'center', alignItems: 'center', margin: '0 8px' }}>
                        {isCurrent ? (
                           <div className="train-marker-animated" style={{
                              width: '24px', height: '24px', borderRadius: '50%',
                              backgroundColor: '#2563eb', // Blue train background
                              display: 'flex', alignItems: 'center', justifyContent: 'center',
                              boxShadow: '0 0 10px rgba(0,0,0,0.3)', zIndex: 3
                           }}>
                              <Train size={14} color="#ffffff" />
                           </div>
                        ) : (
                           <div style={{ 
                             width: '12px', height: '12px', borderRadius: '50%', 
                             background: isPassed ? '#10b981' : '#eab308', 
                             border: '2px solid #ffffff',
                             zIndex: 3
                           }}></div>
                        )}
                      </div>
                      
                      {/* Right: Station Info */}
                      <div style={{ flex: 1, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                          <div style={{ fontSize: '15px', fontWeight: (isFirst || isLast || isCurrent) ? 700 : 600, color: '#0f172a', marginBottom: '2px' }}>
                            {stop[0]}
                          </div>
                          <div style={{ fontSize: '12px', color: '#64748b', fontWeight: 500, display: 'flex', alignItems: 'center', gap: '6px' }}>
                            CODE • {stop[3]} km
                            <span style={{ backgroundColor: '#f1f5f9', border: '1px solid #e2e8f0', color: '#3b82f6', padding: '1px 6px', borderRadius: '4px', fontSize: '10px', fontWeight: 700 }}>PF {pfNumber}</span>
                          </div>
                        </div>
                        
                        {/* Far Right: Departure Time */}
                        <div style={{ textAlign: 'right' }}>
                          <div style={{ fontSize: '13px', fontWeight: 600, color: '#334155' }}>
                            {depTime}
                          </div>
                          {(isDelayed || isEarly) && (
                            <div style={{ fontSize: '12px', fontWeight: 600, color: displayColor }}>
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
                backgroundColor: '#0f172a', color: '#ffffff', 
                borderTopLeftRadius: '24px', borderTopRightRadius: '24px', 
                padding: '20px 16px', boxShadow: '0 -8px 30px rgba(0,0,0,0.2)', zIndex: 10 
              }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '16px' }}>
                  <div>
                    <h3 style={{ margin: 0, fontSize: '16px', fontWeight: 700, color: '#ffffff' }}>Departed {timetable[selectedTrain.train_number]?.s[Math.max(0, selectedTrain.currentStationIndex-1)]?.[0] || 'Origin'}</h3>
                    <div style={{ display: 'flex', gap: '8px', alignItems: 'center', marginTop: '6px' }}>
                      <span style={{ backgroundColor: '#2563eb', color: 'white', padding: '2px 8px', borderRadius: '4px', fontSize: '11px', fontWeight: 800 }}>
                        {selectedTrain.delayMinutes > 0 ? `${selectedTrain.delayMinutes}M LATE` : (selectedTrain.delayMinutes < 0 ? `${Math.abs(selectedTrain.delayMinutes)}M EARLY` : 'ON TIME')}
                      </span>
                      <span style={{ fontSize: '12px', color: '#94a3b8', fontWeight: 500 }}>Updated 1 minute ago</span>
                    </div>
                  </div>
                  <div style={{ width: '36px', height: '36px', borderRadius: '50%', backgroundColor: '#2563eb', display: 'flex', justifyContent: 'center', alignItems: 'center', cursor: 'pointer' }}>
                    <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M21 2v6h-6"></path><path d="M3 12a9 9 0 0 1 15-6.7L21 8"></path><path d="M3 22v-6h6"></path><path d="M21 12a9 9 0 0 1-15 6.7L3 16"></path></svg>
                  </div>
                </div>

                <div style={{ border: '1px solid #334155', borderRadius: '12px', overflow: 'hidden' }}>
                  <div style={{ padding: '12px', display: 'flex', justifyContent: 'space-between', alignItems: 'center', borderBottom: '1px solid #334155' }}>
                    <span style={{ fontSize: '12px', fontWeight: 600 }}>{selectedTrain.dep_station}</span>
                    <div style={{ flex: 1, margin: '0 12px', position: 'relative', height: '4px', backgroundColor: '#334155', borderRadius: '2px' }}>
                      <div style={{ position: 'absolute', left: 0, top: 0, bottom: 0, width: '60%', backgroundColor: '#2563eb', borderRadius: '2px' }}></div>
                      <div style={{ position: 'absolute', left: '60%', top: '-6px', width: '16px', height: '16px', borderRadius: '50%', border: '2px solid #2563eb', backgroundColor: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', transform: 'translateX(-50%)' }}>
                         <Train size={8} color="#2563eb" />
                      </div>
                    </div>
                    <span style={{ fontSize: '12px', fontWeight: 600 }}>{selectedTrain.arr_station}</span>
                  </div>
                  
                  <div style={{ display: 'flex' }}>
                    <div style={{ flex: 1, padding: '12px', borderRight: '1px solid #334155', textAlign: 'center' }}>
                      <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>Next Stop</div>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>{timetable[selectedTrain.train_number]?.s[selectedTrain.currentStationIndex]?.[0] || 'Destination'}</div>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>15km • {new Date().toLocaleTimeString('en-US', {hour: '2-digit', minute:'2-digit'})}</div>
                    </div>
                    <div style={{ flex: 1, padding: '12px', textAlign: 'center' }}>
                      <div style={{ fontSize: '10px', fontWeight: 700, color: '#94a3b8', marginBottom: '4px', textTransform: 'uppercase' }}>To Reach</div>
                      <div style={{ fontSize: '14px', fontWeight: 700, color: '#ffffff', marginBottom: '4px' }}>{selectedTrain.arr_station}</div>
                      <div style={{ fontSize: '11px', color: '#94a3b8' }}>850km • 8:45AM</div>
                    </div>
                  </div>
                  <div style={{ backgroundColor: '#064e3b', color: '#10b981', textAlign: 'center', padding: '8px', fontSize: '12px', fontWeight: 700 }}>
                    ✓ Running {selectedTrain.delayMinutes === 0 ? 'On Time' : (selectedTrain.delayMinutes > 0 ? `${selectedTrain.delayMinutes}m Late` : `${Math.abs(selectedTrain.delayMinutes)}m Early`)}
                  </div>
                </div>
              </div>
            </div>'''

content = content[:start_idx] + new_sidebar + content[end_idx:]

with open('src/pages/MapPage/Map.tsx', 'w', encoding='utf-8') as f:
    f.write(content)

print('Success')
