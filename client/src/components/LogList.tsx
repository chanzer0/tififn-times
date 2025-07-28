import React from 'react';
import { JeccLog } from '../types';
import { format } from 'date-fns';

interface LogListProps {
  logs: JeccLog[];
  total: number;
  page: number;
  perPage: number;
  hasNext: boolean;
  hasPrev: boolean;
  onPageChange: (page: number) => void;
  onLogSelect: (log: JeccLog) => void;
  selectedLog?: JeccLog | null;
}

const LogList: React.FC<LogListProps> = ({
  logs,
  total,
  page,
  perPage,
  hasNext,
  hasPrev,
  onPageChange,
  onLogSelect,
  selectedLog,
}) => {
  return (
    <div>
      <div style={{ marginBottom: '1rem', fontSize: '0.9rem', color: '#a3a3a3' }}>
        Showing {logs.length} of {total} logs {perPage >= 1000 ? '(Recent)' : `(Page ${page})`}
      </div>

      <div className="log-list">
        {logs.map((log) => (
          <div
            key={log.id}
            className={`log-item ${selectedLog?.id === log.id ? 'selected' : ''}`}
            onClick={() => onLogSelect(log)}
          >
            <div className="log-header">
              <span className="cfs-number">CFS #{log.cfs_number || 'N/A'}</span>
              <span className="log-time">
                {format(new Date(log.log_date), 'MM/dd')}
                {log.log_time && ` ${log.log_time}`}
              </span>
            </div>
            
            <div className="log-address">
              {log.address || 'No address'}
            </div>
            
            <div className="log-call-type">
              {log.call_type || 'Unknown call type'}
            </div>
            
            <div className="log-agency">
              {log.agency || 'Unknown agency'}
              {log.disposition && ` • ${log.disposition}`}
            </div>
            
            {log.latitude && log.longitude && (
              <div style={{ fontSize: '0.7rem', color: '#4caf50', marginTop: '0.25rem' }}>
                📍 Geocoded
              </div>
            )}
          </div>
        ))}
      </div>

      {total > perPage && (
        <div className="pagination">
          <button
            onClick={() => onPageChange(page - 1)}
            disabled={!hasPrev}
          >
            Previous
          </button>
          
          <span style={{ margin: '0 1rem', fontSize: '0.9rem' }}>
            Page {page} of {Math.ceil(total / perPage)}
          </span>
          
          <button
            onClick={() => onPageChange(page + 1)}
            disabled={!hasNext}
          >
            Next
          </button>
        </div>
      )}
    </div>
  );
};

export default LogList;