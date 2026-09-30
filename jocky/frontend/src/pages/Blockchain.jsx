import React, { useState } from 'react';
import { api } from '../api/client';

function HashRow({ label, hash, highlight }) {
  if (!hash) return null;
  return (
    <div className="mb-3">
      <div className="text-gray-500 text-xs uppercase tracking-wider mb-1">{label}</div>
      <div className={`font-mono text-xs break-all px-3 py-2 rounded border ${
        highlight === 'green' ? 'bg-green-950 border-green-800 text-green-300' :
        highlight === 'red'   ? 'bg-red-950 border-red-800 text-red-300' :
                                'bg-gray-900 border-gray-700 text-gray-300'
      }`}>
        {hash}
      </div>
    </div>
  );
}

function MatchBadge({ match, detectedAt }) {
  return (
    <div className="mt-4">
      <div className={`flex items-center gap-2 text-sm font-bold px-4 py-3 rounded border ${
        match
          ? 'bg-green-950 border-green-700 text-green-400'
          : 'bg-red-950 border-red-700 text-red-400'
      }`}>
        <span className="text-lg">{match ? '✓' : '✗'}</span>
        <div>
          <div>Match: {match ? 'YES' : 'NO'}</div>
          <div className="text-xs font-normal opacity-80 mt-0.5">
            {match
              ? 'Artifact integrity confirmed — hashes identical'
              : 'TAMPER DETECTED — Immutable ledger record preserved'}
          </div>
        </div>
      </div>
      {!match && detectedAt && (
        <div className="text-xs text-red-400 mt-2 font-mono">
          Detected at: {detectedAt}
        </div>
      )}
    </div>
  );
}

export default function Blockchain() {
  const [evidenceId, setEvidenceId] = useState('E-00421');
  const [verifyResult, setVerifyResult] = useState(null);
  const [tamperResult, setTamperResult] = useState(null);
  const [verifying, setVerifying] = useState(false);
  const [tampering, setTampering] = useState(false);

  async function verify() {
    setVerifying(true);
    try {
      const res = await api.blockchainVerify(evidenceId);
      setVerifyResult(res.data);
    } catch (err) {
      setVerifyResult({ error: err.response?.data?.error || 'Verify failed' });
    } finally {
      setVerifying(false);
    }
  }

  async function runTamperDemo() {
    setTampering(true);
    setTamperResult(null);
    try {
      const res = await api.blockchainTamper(evidenceId);
      setTamperResult(res.data);
    } catch (err) {
      setTamperResult({ error: err.response?.data?.error || 'Tamper demo failed' });
    } finally {
      setTampering(false);
    }
  }

  return (
    <div>
      <h1 className="text-lg font-bold text-gray-200 mb-6">Blockchain Integrity</h1>

      <div className="grid grid-cols-2 gap-6">

        {/* Left: Verify panel */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <div className="text-gray-400 text-xs uppercase tracking-wider mb-4">Verify Evidence</div>

          <div className="flex gap-2 mb-5">
            <input
              value={evidenceId}
              onChange={e => setEvidenceId(e.target.value)}
              className="flex-1 bg-gray-900 border border-gray-700 rounded px-3 py-1.5 text-sm text-gray-200 font-mono focus:outline-none focus:border-green-500"
              placeholder="E-00421"
            />
            <button
              onClick={verify}
              disabled={verifying}
              className="bg-green-700 hover:bg-green-600 disabled:bg-gray-700 text-gray-900 font-bold px-4 py-1.5 rounded text-sm transition-colors"
            >
              {verifying ? '…' : 'Verify'}
            </button>
          </div>

          {verifyResult?.error && (
            <div className="text-red-400 text-xs">{verifyResult.error}</div>
          )}

          {verifyResult && !verifyResult.error && (
            <div>
              <HashRow label="On-chain hash (anchored)" hash={verifyResult.on_chain_hash} highlight="green" />
              <HashRow label="Current hash (recomputed)" hash={verifyResult.current_hash}
                highlight={verifyResult.match ? 'green' : 'red'} />
              <MatchBadge match={verifyResult.match} detectedAt={verifyResult.tamper_detected_at} />
              {verifyResult.anchored_at && (
                <div className="text-xs text-gray-600 mt-2 font-mono">
                  Anchored at: {verifyResult.anchored_at}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right: Tamper demo */}
        <div className="bg-gray-800 border border-gray-700 rounded-lg p-5">
          <div className="text-gray-400 text-xs uppercase tracking-wider mb-3">Tamper Demonstration</div>
          <p className="text-gray-500 text-xs mb-4">
            Appends a tamper flag to evidence data in memory, recomputes the hash, then verifies
            against the immutable ledger record. The on-chain hash doesn't change — the current
            hash does. That difference is the detection.
          </p>
          <button
            onClick={runTamperDemo}
            disabled={tampering}
            className="w-full bg-red-800 hover:bg-red-700 disabled:bg-gray-700 text-gray-200 font-bold py-2 rounded text-sm transition-colors mb-4"
          >
            {tampering ? '⏳ Running…' : '⚠ Run Tamper Demo'}
          </button>

          {tamperResult?.error && (
            <div className="text-red-400 text-xs">{tamperResult.error}</div>
          )}

          {tamperResult && !tamperResult.error && (
            <div>
              <HashRow label="On-chain hash (unchanged)" hash={tamperResult.on_chain_hash} highlight="green" />
              <HashRow label="Current hash (after tamper)" hash={tamperResult.current_hash} highlight="red" />
              <MatchBadge match={false} detectedAt={tamperResult.tamper_detected_at} />
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
