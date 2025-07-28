import React, { useState } from 'react';
import { useLogs } from '../hooks/useLogs';
import { JeccLog } from '../types';
import LogList from '../components/LogList';
import MapComponent from '../components/MapComponent';
import LogFilters from '../components/LogFilters';

const Dashboard: React.FC = () => {
  const { data, loading, error, updateFilters, goToPage } = useLogs({ perPage: 20 });
  const [selectedLog, setSelectedLog] = useState<JeccLog | null>(null);

  if (error) {
    return <div className="error">Error: {error}</div>;
  }

  return (
    <div className="dashboard">
      <div className="sidebar">
        <LogFilters onFiltersChange={updateFilters} />
        {loading ? (
          <div className="loading">Loading logs...</div>
        ) : (
          <LogList
            logs={data?.logs || []}
            total={data?.total || 0}
            page={data?.page || 1}
            perPage={data?.per_page || 20}
            hasNext={data?.has_next || false}
            hasPrev={data?.has_prev || false}
            onPageChange={goToPage}
            onLogSelect={setSelectedLog}
            selectedLog={selectedLog}
          />
        )}
      </div>
      <div className="map-container">
        <MapComponent
          logs={data?.logs || []}
          selectedLog={selectedLog}
          onLogSelect={setSelectedLog}
        />
      </div>
    </div>
  );
};

export default Dashboard;