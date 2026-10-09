import React, { useState } from 'react';
import { Play, Pause, AlertOctagon, Check, X } from 'lucide-react';

export default function StateControls({ currentState, loading, onCommand, getStatusColor }) {
  const [confirmAction, setConfirmAction] = useState(null);

  const handleActionClick = (actionName) => {
    setConfirmAction(actionName);
  };

  const confirmExecution = () => {
    if (confirmAction) {
      onCommand(confirmAction);
      setConfirmAction(null);
    }
  };

  const cancelExecution = () => {
    setConfirmAction(null);
  };

  return (
    <div className="controls-area">
      <div className="status-indicator">
        <div className={`status-dot ${getStatusColor()}`}></div>
        <span style={{ fontWeight: 700, letterSpacing: '0.5px' }}>
          {currentState === 'RUNNING' && 'TRADING ENABLED'}
          {currentState === 'PAUSED' && 'TRADING PAUSED'}
          {currentState === 'EMERGENCY_STOP' && 'EMERGENCY STOP'}
          {currentState !== 'RUNNING' && currentState !== 'PAUSED' && currentState !== 'EMERGENCY_STOP' && 'SYSTEM ONLINE'}
        </span>
      </div>

      {confirmAction ? (
        <div className="confirm-box" style={{ display: 'flex', alignItems: 'center', gap: '8px', background: '#2d1b1b', padding: '4px 10px', borderRadius: '6px', border: '1px solid #e53e3e' }}>
          <span style={{ fontSize: '12px', color: '#feb2b2' }}>Confirm {confirmAction.toUpperCase()}?</span>
          <button
            className="btn btn-emergency"
            style={{ padding: '4px 8px', fontSize: '11px' }}
            onClick={confirmExecution}
            disabled={loading}
          >
            <Check size={12} /> Yes
          </button>
          <button
            className="btn btn-pause"
            style={{ padding: '4px 8px', fontSize: '11px' }}
            onClick={cancelExecution}
          >
            <X size={12} /> No
          </button>
        </div>
      ) : (
        <>
          <button
            className="btn btn-resume"
            onClick={() => handleActionClick('resume')}
            disabled={loading || currentState === 'RUNNING'}
            title="Start automated trading execution"
          >
            <Play size={14} /> START TRADING
          </button>

          <button
            className="btn btn-pause"
            onClick={() => handleActionClick('pause')}
            disabled={loading || currentState === 'PAUSED'}
            title="Pause taking new trades"
          >
            <Pause size={14} /> PAUSE TRADING
          </button>

          <button
            className="btn btn-emergency"
            onClick={() => handleActionClick('emergency-stop')}
            disabled={loading}
            style={{ boxShadow: '0 0 10px rgba(229, 62, 62, 0.4)', fontWeight: 700 }}
            title="Immediate emergency stop: blocks all incoming signals"
          >
            <AlertOctagon size={16} /> EMERGENCY STOP
          </button>
        </>
      )}
    </div>
  );
}

