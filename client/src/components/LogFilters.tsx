import React, { useState } from 'react';
import { LogFilters } from '../types';

interface LogFiltersProps {
  onFiltersChange: (filters: Partial<LogFilters>) => void;
}

const LogFiltersComponent: React.FC<LogFiltersProps> = ({ onFiltersChange }) => {
  const [startDate, setStartDate] = useState('');
  const [endDate, setEndDate] = useState('');
  const [agency, setAgency] = useState('');
  const [callType, setCallType] = useState('');

  const handleFilterChange = () => {
    onFiltersChange({
      startDate: startDate || undefined,
      endDate: endDate || undefined,
      agency: agency || undefined,
      callType: callType || undefined,
    });
  };

  const clearFilters = () => {
    setStartDate('');
    setEndDate('');
    setAgency('');
    setCallType('');
    onFiltersChange({});
  };

  // Common agencies and call types for quick filtering
  const commonAgencies = ['TIFFIN POLICE', 'TIFFIN FIRE', 'SENECA COUNTY SHERIFF', 'STATE HIGHWAY PATROL'];
  const commonCallTypes = ['TRAFFIC STOP', 'MEDICAL', 'FIRE', 'ACCIDENT', 'WELFARE CHECK', 'DOMESTIC'];

  return (
    <div className="filters">
      <h3 style={{ marginBottom: '1rem', color: '#333' }}>Filters</h3>
      
      <div className="filter-group">
        <label>Start Date:</label>
        <input
          type="date"
          value={startDate}
          onChange={(e) => setStartDate(e.target.value)}
          onBlur={handleFilterChange}
        />
      </div>

      <div className="filter-group">
        <label>End Date:</label>
        <input
          type="date"
          value={endDate}
          onChange={(e) => setEndDate(e.target.value)}
          onBlur={handleFilterChange}
        />
      </div>

      <div className="filter-group">
        <label>Agency:</label>
        <select
          value={agency}
          onChange={(e) => {
            setAgency(e.target.value);
            onFiltersChange({ agency: e.target.value || undefined });
          }}
        >
          <option value="">All Agencies</option>
          {commonAgencies.map((ag) => (
            <option key={ag} value={ag}>{ag}</option>
          ))}
        </select>
      </div>

      <div className="filter-group">
        <label>Call Type:</label>
        <select
          value={callType}
          onChange={(e) => {
            setCallType(e.target.value);
            onFiltersChange({ callType: e.target.value || undefined });
          }}
        >
          <option value="">All Call Types</option>
          {commonCallTypes.map((ct) => (
            <option key={ct} value={ct}>{ct}</option>
          ))}
        </select>
      </div>

      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1rem' }}>
        <button
          onClick={handleFilterChange}
          style={{ flex: 1, backgroundColor: '#1976d2', color: 'white', border: 'none' }}
        >
          Apply Filters
        </button>
        <button
          onClick={clearFilters}
          style={{ flex: 1, backgroundColor: '#666', color: 'white', border: 'none' }}
        >
          Clear
        </button>
      </div>
    </div>
  );
};

export default LogFiltersComponent;