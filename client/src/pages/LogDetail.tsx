import React from 'react';
import { useParams, Link } from 'react-router-dom';
import { useLog } from '../hooks/useLog';
import { format } from 'date-fns';

const LogDetail: React.FC = () => {
  const { id } = useParams<{ id: string }>();
  const { data: log, loading, error } = useLog(Number(id));

  if (loading) {
    return <div className="loading">Loading log details...</div>;
  }

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  if (!log) {
    return <div className="error">Log not found</div>;
  }

  return (
    <div className="container">
      <div style={{ marginBottom: '1rem' }}>
        <Link to="/" style={{ color: '#1976d2', textDecoration: 'none' }}>
          ← Back to Dashboard
        </Link>
      </div>
      
      <div style={{ backgroundColor: 'white', padding: '2rem', borderRadius: '8px', boxShadow: '0 2px 4px rgba(0,0,0,0.1)' }}>
        <h2 style={{ marginBottom: '1.5rem', color: '#333' }}>
          Call Details - CFS #{log.cfs_number}
        </h2>
        
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '2rem' }}>
          <div>
            <h3 style={{ marginBottom: '1rem', color: '#666' }}>Call Information</h3>
            <p><strong>Date:</strong> {format(new Date(log.log_date), 'MM/dd/yyyy')}</p>
            {log.log_time && <p><strong>Time:</strong> {log.log_time}</p>}
            <p><strong>Call Type:</strong> {log.call_type || 'N/A'}</p>
            <p><strong>Agency:</strong> {log.agency || 'N/A'}</p>
            <p><strong>Disposition:</strong> {log.disposition || 'N/A'}</p>
            {log.incident_number && <p><strong>Incident #:</strong> {log.incident_number}</p>}
          </div>
          
          <div>
            <h3 style={{ marginBottom: '1rem', color: '#666' }}>Location Information</h3>
            <p><strong>Address:</strong> {log.address || 'N/A'}</p>
            {log.apt_suite && <p><strong>Apt/Suite:</strong> {log.apt_suite}</p>}
            {log.latitude && log.longitude && (
              <>
                <p><strong>Coordinates:</strong> {log.latitude}, {log.longitude}</p>
                {log.geocoded_address && (
                  <p><strong>Geocoded Address:</strong> {log.geocoded_address}</p>
                )}
                {log.geocoded_at && (
                  <p><strong>Geocoded:</strong> {format(new Date(log.geocoded_at), 'MM/dd/yyyy HH:mm')}</p>
                )}
              </>
            )}
          </div>
        </div>
        
        <div style={{ borderTop: '1px solid #eee', paddingTop: '1rem' }}>
          <h3 style={{ marginBottom: '1rem', color: '#666' }}>Record Information</h3>
          <p><strong>Created:</strong> {format(new Date(log.created_at), 'MM/dd/yyyy HH:mm')}</p>
          <p><strong>Updated:</strong> {format(new Date(log.updated_at), 'MM/dd/yyyy HH:mm')}</p>
        </div>
      </div>
    </div>
  );
};

export default LogDetail;