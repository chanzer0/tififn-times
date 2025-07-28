import React, { useEffect, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, useMap } from 'react-leaflet';
import L from 'leaflet';
import { JeccLog } from '../types';
import 'leaflet/dist/leaflet.css';

// Fix for default markers in React-Leaflet
delete (L.Icon.Default.prototype as any)._getIconUrl;
L.Icon.Default.mergeOptions({
  iconRetinaUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon-2x.png',
  iconUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-icon.png',
  shadowUrl: 'https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.7.1/images/marker-shadow.png',
});

// Custom icons for different call types
const createIcon = (callType?: string, count: number = 1) => {
  let color = '#1976d2'; // default blue
  
  if (callType) {
    const type = callType.toLowerCase();
    if (type.includes('fire')) color = '#d32f2f'; // red
    else if (type.includes('medical')) color = '#388e3c'; // green
    else if (type.includes('traffic')) color = '#f57c00'; // orange
    else if (type.includes('accident')) color = '#7b1fa2'; // purple
  }
  
  const size = count > 1 ? 32 : 24;
  const fontSize = count > 1 ? '12px' : '0px';
  const fontWeight = count > 1 ? '700' : 'normal';
  
  return L.divIcon({
    className: 'custom-marker',
    html: `<div style="
      background-color: ${color};
      width: ${size}px;
      height: ${size}px;
      border-radius: 50%;
      border: 3px solid #1a1a1a;
      box-shadow: 0 4px 12px rgba(0,0,0,0.6), 0 0 0 1px rgba(255,255,255,0.1);
      transition: all 0.2s ease;
      display: flex;
      align-items: center;
      justify-content: center;
      color: white;
      font-size: ${fontSize};
      font-weight: ${fontWeight};
      text-shadow: 0 1px 2px rgba(0,0,0,0.8);
    ">${count > 1 ? count : ''}</div>`,
    iconSize: [size, size],
    iconAnchor: [size / 2, size / 2],
  });
};

interface MapComponentProps {
  logs: JeccLog[];
  selectedLog?: JeccLog | null;
  onLogSelect: (log: JeccLog) => void;
}

// Component to handle map updates when selectedLog changes
const MapUpdater: React.FC<{ selectedLog?: JeccLog | null }> = ({ selectedLog }) => {
  const map = useMap();

  useEffect(() => {
    if (selectedLog && selectedLog.latitude && selectedLog.longitude) {
      map.setView([selectedLog.latitude, selectedLog.longitude], 16);
    }
  }, [selectedLog, map]);

  return null;
};

const MapComponent: React.FC<MapComponentProps> = ({ logs, selectedLog, onLogSelect }) => {
  const [center, setCenter] = useState<[number, number]>([41.6611, -91.5254]); // Tiffin, IA (Johnson County)
  const [zoom, setZoom] = useState(12);

  // Filter logs that have coordinates and convert strings to numbers
  const logsWithCoordinates = logs.filter(log => {
    const lat = typeof log.latitude === 'string' ? parseFloat(log.latitude) : log.latitude;
    const lng = typeof log.longitude === 'string' ? parseFloat(log.longitude) : log.longitude;
    return lat && lng && !isNaN(lat) && !isNaN(lng);
  }).map(log => ({
    ...log,
    latitude: typeof log.latitude === 'string' ? parseFloat(log.latitude) : log.latitude,
    longitude: typeof log.longitude === 'string' ? parseFloat(log.longitude) : log.longitude,
  }));

  // Group logs by coordinates (clustering)
  const clusteredLogs = logsWithCoordinates.reduce((clusters, log) => {
    const key = `${log.latitude?.toFixed(6)},${log.longitude?.toFixed(6)}`;
    if (!clusters[key]) {
      clusters[key] = [];
    }
    clusters[key].push(log);
    return clusters;
  }, {} as Record<string, typeof logsWithCoordinates>);

  // Convert clusters to array with cluster info
  const clusterData = Object.values(clusteredLogs).map(clusterLogs => ({
    logs: clusterLogs,
    position: [clusterLogs[0].latitude!, clusterLogs[0].longitude!] as [number, number],
    count: clusterLogs.length,
    primaryCallType: clusterLogs[0].call_type // Use first log's call type for pin color
  }));

  // Log pin statistics
  console.log(`📍 Displaying ${clusterData.length} pins (${logsWithCoordinates.length} total logs with coordinates)`);

  // Update map center based on available logs
  useEffect(() => {
    if (logsWithCoordinates.length > 0) {
      // Calculate center of all logs
      const avgLat = logsWithCoordinates.reduce((sum, log) => sum + (log.latitude || 0), 0) / logsWithCoordinates.length;
      const avgLng = logsWithCoordinates.reduce((sum, log) => sum + (log.longitude || 0), 0) / logsWithCoordinates.length;
      setCenter([avgLat, avgLng]);
    }
  }, [logs.length]); // Only depend on logs array length, not the processed array

  const formatDate = (dateStr: string) => {
    return new Date(dateStr).toLocaleDateString();
  };

  // Group logs by call type and disposition for popup
  const groupLogsByCategory = (logs: JeccLog[]) => {
    const grouped = logs.reduce((groups, log) => {
      const callType = log.call_type || 'Unknown';
      const disposition = log.disposition || 'Unknown';
      
      if (!groups[callType]) {
        groups[callType] = {};
      }
      if (!groups[callType][disposition]) {
        groups[callType][disposition] = [];
      }
      groups[callType][disposition].push(log);
      
      return groups;
    }, {} as Record<string, Record<string, JeccLog[]>>);
    
    return grouped;
  };

  // Create popup content for clustered logs
  const createClusterPopup = (logs: JeccLog[]) => {
    if (logs.length === 1) {
      // Single log - use existing popup
      const log = logs[0];
      return (
        <div style={{ 
          minWidth: '240px', 
          padding: '8px',
          backgroundColor: '#1a1a1a',
          color: '#e0e0e0',
          borderRadius: '8px',
          border: '1px solid #333'
        }}>
          <h4 style={{ 
            margin: '0 0 0.75rem 0', 
            color: '#60a5fa',
            fontSize: '1.1rem',
            fontWeight: '600'
          }}>
            CFS #{log.cfs_number || 'N/A'}
          </h4>
          
          <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
            <strong style={{ color: '#a3a3a3' }}>Date:</strong>{' '}
            <span style={{ color: '#e0e0e0' }}>{formatDate(log.log_date)}</span>
            {log.log_time && <span style={{ color: '#e0e0e0' }}> at {log.log_time}</span>}
          </div>
          
          <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
            <strong style={{ color: '#a3a3a3' }}>Address:</strong>{' '}
            <span style={{ color: '#e0e0e0' }}>{log.address || 'Unknown'}</span>
            {log.apt_suite && <span style={{ color: '#e0e0e0' }}>, {log.apt_suite}</span>}
          </div>
          
          {log.geocoded_address && log.geocoded_address !== log.address && (
            <div style={{ marginBottom: '0.5rem', fontSize: '0.85rem' }}>
              <strong style={{ color: '#a3a3a3' }}>Geocoded:</strong>{' '}
              <span style={{ color: '#10b981', fontStyle: 'italic' }}>{log.geocoded_address}</span>
            </div>
          )}
          
          <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
            <strong style={{ color: '#a3a3a3' }}>Call Type:</strong>{' '}
            <span style={{ color: '#fbbf24' }}>{log.call_type || 'Unknown'}</span>
          </div>
          
          <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
            <strong style={{ color: '#a3a3a3' }}>Agency:</strong>{' '}
            <span style={{ color: '#e0e0e0' }}>{log.agency || 'Unknown'}</span>
          </div>
          
          {log.disposition && (
            <div style={{ marginBottom: '0.5rem', fontSize: '0.9rem' }}>
              <strong style={{ color: '#a3a3a3' }}>Disposition:</strong>{' '}
              <span style={{ color: '#10b981' }}>{log.disposition}</span>
            </div>
          )}
          
          <div style={{ 
            fontSize: '0.75rem', 
            color: '#6b7280', 
            marginTop: '0.75rem',
            fontStyle: 'italic'
          }}>
            Click marker to select this log
          </div>
        </div>
      );
    }

    // Multiple logs - show grouped view
    const grouped = groupLogsByCategory(logs);
    
    return (
      <div style={{ 
        minWidth: '320px',
        maxWidth: '400px',
        padding: '12px',
        backgroundColor: '#1a1a1a',
        color: '#e0e0e0',
        borderRadius: '8px',
        border: '1px solid #333',
        maxHeight: '400px',
        overflowY: 'auto'
      }}>
        <h4 style={{ 
          margin: '0 0 1rem 0', 
          color: '#60a5fa',
          fontSize: '1.2rem',
          fontWeight: '600'
        }}>
          {logs.length} Emergency Calls
        </h4>
        
        <div style={{ marginBottom: '0.75rem', fontSize: '0.9rem' }}>
          <strong style={{ color: '#a3a3a3' }}>Address:</strong>{' '}
          <span style={{ color: '#e0e0e0' }}>{logs[0].address || 'Unknown'}</span>
        </div>
        
        {logs[0].geocoded_address && logs[0].geocoded_address !== logs[0].address && (
          <div style={{ marginBottom: '0.75rem', fontSize: '0.85rem' }}>
            <strong style={{ color: '#a3a3a3' }}>Geocoded:</strong>{' '}
            <span style={{ color: '#10b981', fontStyle: 'italic' }}>{logs[0].geocoded_address}</span>
          </div>
        )}
        
        {Object.entries(grouped).map(([callType, dispositions]) => (
          <details key={callType} style={{ marginBottom: '0.75rem' }}>
            <summary style={{ 
              color: '#fbbf24', 
              fontWeight: '600',
              cursor: 'pointer',
              fontSize: '0.95rem',
              marginBottom: '0.5rem'
            }}>
              {callType} ({Object.values(dispositions).reduce((sum, logs) => sum + logs.length, 0)})
            </summary>
            
            {Object.entries(dispositions).map(([disposition, dispLogs]) => (
              <details key={disposition} style={{ marginLeft: '1rem', marginBottom: '0.5rem' }}>
                <summary style={{ 
                  color: '#10b981', 
                  fontWeight: '500',
                  cursor: 'pointer',
                  fontSize: '0.85rem'
                }}>
                  {disposition} ({dispLogs.length})
                </summary>
                
                <div style={{ marginLeft: '1rem', marginTop: '0.5rem' }}>
                  {dispLogs.map((log, idx) => (
                    <div 
                      key={log.id} 
                      style={{ 
                        marginBottom: '0.5rem',
                        padding: '0.5rem',
                        backgroundColor: '#262626',
                        borderRadius: '4px',
                        fontSize: '0.8rem',
                        cursor: 'pointer',
                        border: '1px solid #404040'
                      }}
                      onClick={() => onLogSelect(log)}
                    >
                      <div style={{ color: '#60a5fa', fontWeight: '600' }}>
                        CFS #{log.cfs_number || 'N/A'}
                      </div>
                      <div style={{ color: '#a3a3a3' }}>
                        {formatDate(log.log_date)} {log.log_time}
                      </div>
                      <div style={{ color: '#e0e0e0' }}>
                        {log.agency}
                      </div>
                    </div>
                  ))}
                </div>
              </details>
            ))}
          </details>
        ))}
        
        <div style={{ 
          fontSize: '0.75rem', 
          color: '#6b7280', 
          marginTop: '0.75rem',
          fontStyle: 'italic'
        }}>
          Click individual calls to select them
        </div>
      </div>
    );
  };

  return (
    <MapContainer
      center={center}
      zoom={zoom}
      style={{ height: '100%', width: '100%' }}
      scrollWheelZoom={true}
    >
      <TileLayer
        attribution='&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors'
        url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
      />
      
      <MapUpdater selectedLog={selectedLog} />
      
      {clusterData.map((cluster, index) => (
        <Marker
          key={`cluster-${index}-${cluster.position[0]}-${cluster.position[1]}`}
          position={cluster.position}
          icon={createIcon(cluster.primaryCallType, cluster.count)}
          eventHandlers={{
            click: () => {
              // If single log, select it directly
              if (cluster.count === 1) {
                onLogSelect(cluster.logs[0]);
              }
              // For multiple logs, the popup will handle selection
            },
          }}
        >
          <Popup>
            {createClusterPopup(cluster.logs)}
          </Popup>
        </Marker>
      ))}
    </MapContainer>
  );
};

export default MapComponent;