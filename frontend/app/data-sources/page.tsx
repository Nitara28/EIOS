'use client';

import React, { useState, useEffect } from 'react';
import { Database, FileSpreadsheet, Mail, MessageSquare, Building, Upload, CheckCircle2, ArrowRight, AlertCircle, RefreshCw, ExternalLink, Settings, X, Send, Phone } from 'lucide-react';
import { uploadApi, fetchApi } from '@/lib/api';

export default function DataSourcesPage() {
  const [connectors, setConnectors] = useState<any[]>([]);
  const [file, setFile] = useState<File | null>(null);
  const [preview, setPreview] = useState<any>(null);
  const [columnMapping, setColumnMapping] = useState<Record<string, string>>({});
  const [uploading, setUploading] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const [step, setStep] = useState<1 | 2 | 3>(1);
  const [gmailStatus, setGmailStatus] = useState<any>(null);
  const [syncingGmail, setSyncingGmail] = useState(false);

  // WhatsApp state
  const [waModalOpen, setWaModalOpen] = useState(false);
  const [waSendModalOpen, setWaSendModalOpen] = useState(false);
  const [waPhoneId, setWaPhoneId] = useState('');
  const [waAccessToken, setWaAccessToken] = useState('');
  const [waVerifyToken, setWaVerifyToken] = useState('eios_whatsapp_verify_token');
  const [waBusinessAccId, setWaBusinessAccId] = useState('');
  const [waStatusMsg, setWaStatusMsg] = useState<string | null>(null);
  const [waTestPhone, setWaTestPhone] = useState('');
  const [waTestMsg, setWaTestMsg] = useState('Hello! This is an automated test payment reminder from EIOS AI COO.');
  const [waSendStatus, setWaSendStatus] = useState<any>(null);

  useEffect(() => {
    loadConnectors();
  }, []);

  async function loadConnectors() {
    try {
      const data = await fetchApi('/connectors');
      setConnectors(data);
    } catch (err) {
      console.error('Failed to load connectors:', err);
    }
  }

  const handleConnectGmail = async () => {
    try {
      const data = await fetchApi('/connectors/gmail/auth-url');
      if (data.configured && data.authorization_url) {
        window.location.href = data.authorization_url;
      } else {
        alert(data.error || 'GOOGLE_CLIENT_ID is not configured in backend environment variables.');
      }
    } catch (err: any) {
      alert(`Gmail Connect Error: ${err.message}`);
    }
  };

  const handleSyncGmail = async () => {
    try {
      setSyncingGmail(true);
      const res = await fetchApi('/connectors/gmail/sync', { method: 'POST' });
      setGmailStatus(res);
      await loadConnectors();
    } catch (err: any) {
      setGmailStatus({ status: 'ERROR', summary: err.message });
    } finally {
      setSyncingGmail(false);
    }
  };

  const handleSaveWhatsAppConfig = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setWaStatusMsg('Saving WhatsApp configuration...');
      const res = await fetchApi('/connectors/whatsapp/configure', {
        method: 'POST',
        body: JSON.stringify({
          access_token: waAccessToken,
          phone_number_id: waPhoneId,
          business_account_id: waBusinessAccId,
          verify_token: waVerifyToken
        })
      });
      setWaStatusMsg('WhatsApp Business API configured successfully!');
      setWaModalOpen(false);
      await loadConnectors();
    } catch (err: any) {
      setWaStatusMsg(`Configuration failed: ${err.message}`);
    }
  };

  const handleSendWhatsAppTest = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      setWaSendStatus({ status: 'SENDING', message: 'Dispatching WhatsApp message via Meta Graph API...' });
      const res = await fetchApi('/connectors/whatsapp/send', {
        method: 'POST',
        body: JSON.stringify({
          recipient_phone: waTestPhone,
          message: waTestMsg
        })
      });
      setWaSendStatus(res);
      await loadConnectors();
    } catch (err: any) {
      setWaSendStatus({ success: false, error_code: 'WHATSAPP_API_ERROR', message: err.message });
    }
  };

  const handleDisconnectWhatsApp = async () => {
    try {
      await fetchApi('/connectors/whatsapp/disconnect', { method: 'POST' });
      await loadConnectors();
      setWaStatusMsg('WhatsApp Business API disconnected.');
    } catch (err: any) {
      alert(`Disconnect failed: ${err.message}`);
    }
  };

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      const selected = e.target.files[0];
      setFile(selected);

      const formData = new FormData();
      formData.append('file', selected);
      try {
        setUploading(true);
        const res = await uploadApi('/connectors/preview', formData);
        setPreview(res);
        setColumnMapping(res.suggested_mapping || {});
        setStep(2);
      } catch (err: any) {
        alert(`Preview failed: ${err.message}`);
      } finally {
        setUploading(false);
      }
    }
  };

  const handleExecuteImport = async () => {
    if (!file) return;

    try {
      setUploading(true);
      const formData = new FormData();
      formData.append('file', file);
      formData.append('column_mapping', JSON.stringify(columnMapping));

      const res = await uploadApi('/connectors/upload', formData);
      setImportResult(res);
      setStep(3);
    } catch (err: any) {
      alert(`Import failed: ${err.message}`);
    } finally {
      setUploading(false);
    }
  };

  const gmailConn = connectors.find(c => c.source_type === 'GMAIL');
  const waConn = connectors.find(c => c.source_type === 'WHATSAPP');

  return (
    <div className="space-y-6">
      {/* Header */}
      <div>
        <h1 className="text-2xl font-bold text-white tracking-wide">Data Source Connectors</h1>
        <p className="text-sm text-slate-400 mt-1">Connect business systems, upload spreadsheets, and sync operational data into EIOS</p>
      </div>

      {/* Interactive Excel / CSV Upload Wizard */}
      <div className="p-6 rounded-2xl bg-[#111827] border border-emerald-500/30 shadow-2xl space-y-6">
        <div className="flex items-center justify-between border-b border-slate-800 pb-4">
          <div className="flex items-center space-x-3">
            <div className="w-10 h-10 rounded-xl bg-emerald-500/20 border border-emerald-500/40 flex items-center justify-center text-emerald-400">
              <FileSpreadsheet className="w-5 h-5" />
            </div>
            <div>
              <h2 className="text-base font-bold text-white">Excel & CSV Data Connector Wizard</h2>
              <p className="text-xs text-slate-400">Upload customer lists, project rosters, or overdue invoice spreadsheets</p>
            </div>
          </div>

          <div className="flex items-center space-x-2 text-xs">
            <span className={`px-2.5 py-1 rounded font-bold ${step === 1 ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-400'}`}>1. Select File</span>
            <span className={`px-2.5 py-1 rounded font-bold ${step === 2 ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-400'}`}>2. Map Columns</span>
            <span className={`px-2.5 py-1 rounded font-bold ${step === 3 ? 'bg-emerald-500 text-slate-950' : 'bg-slate-800 text-slate-400'}`}>3. Summary</span>
          </div>
        </div>

        {/* Step 1: Upload Box */}
        {step === 1 && (
          <div className="border-2 border-dashed border-slate-800 hover:border-emerald-500/50 rounded-2xl p-8 text-center transition cursor-pointer bg-slate-950/40">
            <input
              type="file"
              accept=".csv, .xlsx, .xls"
              onChange={handleFileSelect}
              className="hidden"
              id="file-upload"
            />
            <label htmlFor="file-upload" className="cursor-pointer space-y-3 block">
              <Upload className="w-10 h-10 mx-auto text-emerald-400 animate-bounce" />
              <div>
                <p className="text-sm font-bold text-white">Click to upload spreadsheet file</p>
                <p className="text-xs text-slate-400 mt-1">Supports .xlsx, .xls, and .csv formats</p>
              </div>
            </label>
          </div>
        )}

        {/* Step 2: Mapping & Preview */}
        {step === 2 && preview && (
          <div className="space-y-4">
            <div className="flex items-center justify-between text-xs text-slate-300 bg-slate-900 p-3 rounded-xl border border-slate-800">
              <span>Detected File: <strong>{preview.filename}</strong> ({preview.total_rows} rows)</span>
              <button onClick={() => setStep(1)} className="text-emerald-400 hover:underline font-semibold">Change File</button>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div className="space-y-3 bg-slate-900/50 p-4 rounded-xl border border-slate-800">
                <h3 className="text-xs font-bold text-emerald-400 uppercase tracking-wider">Field Mapping</h3>
                {['name', 'company_name', 'email', 'phone', 'amount', 'due_date'].map((field) => (
                  <div key={field} className="flex items-center justify-between text-xs">
                    <span className="text-slate-400 capitalize">{field.replace('_', ' ')}:</span>
                    <select
                      value={columnMapping[field] || ''}
                      onChange={(e) => setColumnMapping({ ...columnMapping, [field]: e.target.value })}
                      className="bg-slate-950 border border-slate-800 rounded px-2 py-1 text-slate-200 text-xs"
                    >
                      <option value="">-- Unmapped --</option>
                      {preview.headers.map((h: string) => (
                        <option key={h} value={h}>{h}</option>
                      ))}
                    </select>
                  </div>
                ))}
              </div>

              {/* Sample Data Table */}
              <div className="bg-slate-900/50 p-4 rounded-xl border border-slate-800 overflow-x-auto">
                <h3 className="text-xs font-bold text-slate-300 uppercase tracking-wider mb-2">Sample Preview</h3>
                <table className="w-full text-[11px] text-left">
                  <thead className="text-slate-400 border-b border-slate-800">
                    <tr>
                      {preview.headers.slice(0, 4).map((h: string) => (
                        <th key={h} className="p-1">{h}</th>
                      ))}
                    </tr>
                  </thead>
                  <tbody className="divide-y divide-slate-800/60">
                    {preview.sample_rows.slice(0, 3).map((row: any, i: number) => (
                      <tr key={i}>
                        {preview.headers.slice(0, 4).map((h: string) => (
                          <td key={h} className="p-1 text-slate-300 truncate max-w-[100px]">{String(row[h])}</td>
                        ))}
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>

            <div className="flex justify-end pt-2">
              <button
                disabled={uploading}
                onClick={handleExecuteImport}
                className="px-6 py-2.5 rounded-xl bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs flex items-center space-x-2 transition"
              >
                <span>{uploading ? 'Importing Data...' : 'Confirm & Execute Import'}</span>
                <ArrowRight className="w-4 h-4" />
              </button>
            </div>
          </div>
        )}

        {/* Step 3: Import Results */}
        {step === 3 && importResult && (
          <div className="p-6 rounded-xl bg-emerald-500/10 border border-emerald-500/30 text-center space-y-4">
            <CheckCircle2 className="w-12 h-12 text-emerald-400 mx-auto" />
            <h3 className="text-lg font-bold text-white">Import Execution Completed</h3>
            <p className="text-xs text-slate-300">{importResult.summary}</p>

            <div className="grid grid-cols-4 gap-2 text-center text-xs pt-2">
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Processed</span>
                <strong className="text-white text-sm">{importResult.records_processed}</strong>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Imported</span>
                <strong className="text-emerald-400 text-sm">{importResult.records_imported}</strong>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Duplicates</span>
                <strong className="text-amber-400 text-sm">{importResult.duplicates_matched}</strong>
              </div>
              <div className="p-2 rounded bg-slate-900 border border-slate-800">
                <span className="text-slate-500 block text-[10px]">Errors</span>
                <strong className="text-rose-400 text-sm">{importResult.errors_count}</strong>
              </div>
            </div>

            <button
              onClick={() => { setStep(1); setFile(null); setPreview(null); }}
              className="mt-4 px-4 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 text-slate-200 text-xs font-semibold"
            >
              Upload Another File
            </button>
          </div>
        )}
      </div>

      {/* Grid of Modular External Connectors */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {/* Real Gmail OAuth Connector */}
        <div className="p-5 rounded-2xl bg-[#111827] border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-xl bg-blue-500/10 text-blue-400 flex items-center justify-center mb-3">
              <Mail className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-white text-sm">Gmail Business Connector</h3>
            <p className="text-xs text-slate-400 mt-1">Sync customer email threads & match senders to customer profiles via Google OAuth 2.0.</p>

            {gmailStatus && (
              <div className="mt-3 p-2 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300">
                <p className="font-bold text-amber-400">Status: {gmailStatus.status}</p>
                <p className="text-[10px] text-slate-400 mt-0.5">{gmailStatus.summary}</p>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-center text-xs">
            <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${
              gmailConn?.configured ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-amber-400'
            }`}>
              {gmailConn?.configured ? 'CONNECTED' : 'UNCONFIGURED'}
            </span>

            <div className="flex items-center space-x-2">
              <button
                onClick={handleSyncGmail}
                disabled={syncingGmail}
                className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 flex items-center space-x-1"
              >
                <RefreshCw className={`w-3 h-3 ${syncingGmail ? 'animate-spin' : ''}`} />
                <span>Sync</span>
              </button>

              <button
                onClick={handleConnectGmail}
                className="px-2.5 py-1 rounded bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs flex items-center space-x-1"
              >
                <span>Authorize</span>
                <ExternalLink className="w-3 h-3" />
              </button>
            </div>
          </div>
        </div>

        {/* WhatsApp Business Cloud API */}
        <div className="p-5 rounded-2xl bg-[#111827] border border-slate-800 flex flex-col justify-between">
          <div>
            <div className="w-10 h-10 rounded-xl bg-emerald-500/10 text-emerald-400 flex items-center justify-center mb-3">
              <MessageSquare className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-white text-sm">WhatsApp Business Cloud API</h3>
            <p className="text-xs text-slate-400 mt-1">Send payment reminders, parse incoming customer webhooks & match phone numbers.</p>

            {waStatusMsg && (
              <div className="mt-3 p-2 rounded bg-slate-950 border border-slate-800 text-[11px] text-slate-300">
                <p className="text-emerald-400 font-medium">{waStatusMsg}</p>
              </div>
            )}
          </div>

          <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-center text-xs">
            <span className={`px-2 py-0.5 rounded font-mono text-[10px] ${
              waConn?.configured ? 'bg-emerald-500/20 text-emerald-400' : 'bg-slate-800 text-amber-400'
            }`}>
              {waConn?.configured ? 'CONNECTED' : 'UNCONFIGURED'}
            </span>

            <div className="flex items-center space-x-2">
              {waConn?.configured && (
                <button
                  onClick={() => setWaSendModalOpen(true)}
                  className="px-2.5 py-1 rounded bg-slate-800 hover:bg-slate-700 text-slate-200 font-semibold text-xs border border-slate-700 flex items-center space-x-1"
                >
                  <Send className="w-3 h-3 text-emerald-400" />
                  <span>Send</span>
                </button>
              )}

              <button
                onClick={() => setWaModalOpen(true)}
                className="px-2.5 py-1 rounded bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold text-xs flex items-center space-x-1"
              >
                <Settings className="w-3 h-3" />
                <span>Configure</span>
              </button>
            </div>
          </div>
        </div>

        {/* Tally Prime */}
        <div className="p-5 rounded-2xl bg-[#111827] border border-slate-800 flex flex-col justify-between opacity-80">
          <div>
            <div className="w-10 h-10 rounded-xl bg-amber-500/10 text-amber-400 flex items-center justify-center mb-3">
              <Building className="w-5 h-5" />
            </div>
            <h3 className="font-bold text-white text-sm">Tally Prime Direct Sync</h3>
            <p className="text-xs text-slate-400 mt-1">Automatic direct sync for ledgers, vouchers, and receivables from Tally.</p>
          </div>
          <div className="mt-4 pt-3 border-t border-slate-800 flex justify-between items-center text-xs">
            <span className="px-2 py-0.5 rounded bg-slate-800 text-amber-400 font-mono text-[10px]">CONFIG READY</span>
            <button className="text-slate-500 font-semibold cursor-not-allowed">Setup Sync</button>
          </div>
        </div>
      </div>

      {/* WhatsApp Configure Modal */}
      {waModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-[#111827] border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2 text-emerald-400">
                <MessageSquare className="w-5 h-5" />
                <h3 className="font-bold text-white text-sm">Configure WhatsApp Business API</h3>
              </div>
              <button onClick={() => setWaModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSaveWhatsAppConfig} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Phone Number ID *</label>
                <input
                  type="text"
                  required
                  placeholder="e.g. 109283746509182"
                  value={waPhoneId}
                  onChange={(e) => setWaPhoneId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Meta Permanent Access Token *</label>
                <input
                  type="password"
                  required
                  placeholder="EAAG..."
                  value={waAccessToken}
                  onChange={(e) => setWaAccessToken(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Business Account ID (Optional)</label>
                <input
                  type="text"
                  placeholder="e.g. 9876543210123"
                  value={waBusinessAccId}
                  onChange={(e) => setWaBusinessAccId(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 placeholder-slate-600 focus:outline-none focus:border-emerald-500"
                />
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Webhook Verify Token</label>
                <input
                  type="text"
                  value={waVerifyToken}
                  onChange={(e) => setWaVerifyToken(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg px-3 py-2 text-slate-100 focus:outline-none focus:border-emerald-500 font-mono"
                />
              </div>

              <div className="pt-3 flex justify-between items-center">
                {waConn?.configured && (
                  <button
                    type="button"
                    onClick={handleDisconnectWhatsApp}
                    className="text-rose-400 hover:underline font-semibold text-xs"
                  >
                    Disconnect Account
                  </button>
                )}
                <div className="flex space-x-2 ml-auto">
                  <button
                    type="button"
                    onClick={() => setWaModalOpen(false)}
                    className="px-3 py-2 rounded-lg bg-slate-800 text-slate-300 font-semibold hover:bg-slate-700"
                  >
                    Cancel
                  </button>
                  <button
                    type="submit"
                    className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold"
                  >
                    Save Credentials
                  </button>
                </div>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* WhatsApp Test Message Modal */}
      {waSendModalOpen && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-black/70 backdrop-blur-sm p-4">
          <div className="w-full max-w-md bg-[#111827] border border-slate-800 rounded-2xl p-6 shadow-2xl space-y-4">
            <div className="flex items-center justify-between border-b border-slate-800 pb-3">
              <div className="flex items-center space-x-2 text-emerald-400">
                <Send className="w-5 h-5" />
                <h3 className="font-bold text-white text-sm">Send Outbound WhatsApp Message</h3>
              </div>
              <button onClick={() => setWaSendModalOpen(false)} className="text-slate-400 hover:text-white">
                <X className="w-5 h-5" />
              </button>
            </div>

            <form onSubmit={handleSendWhatsAppTest} className="space-y-3 text-xs">
              <div>
                <label className="block text-slate-400 font-semibold mb-1">Recipient Phone Number *</label>
                <div className="relative">
                  <Phone className="w-4 h-4 text-slate-500 absolute left-3 top-1/2 -translate-y-1/2" />
                  <input
                    type="text"
                    required
                    placeholder="+91 98765 43210"
                    value={waTestPhone}
                    onChange={(e) => setWaTestPhone(e.target.value)}
                    className="w-full bg-slate-900 border border-slate-800 rounded-lg pl-9 pr-3 py-2 text-slate-100 focus:outline-none focus:border-emerald-500"
                  />
                </div>
              </div>

              <div>
                <label className="block text-slate-400 font-semibold mb-1">Message Body *</label>
                <textarea
                  required
                  rows={3}
                  value={waTestMsg}
                  onChange={(e) => setWaTestMsg(e.target.value)}
                  className="w-full bg-slate-900 border border-slate-800 rounded-lg p-3 text-slate-100 focus:outline-none focus:border-emerald-500"
                />
              </div>

              {waSendStatus && (
                <div className={`p-3 rounded-lg text-xs font-mono border ${
                  waSendStatus.success ? 'bg-emerald-500/10 border-emerald-500/30 text-emerald-300' : 'bg-rose-500/10 border-rose-500/30 text-rose-300'
                }`}>
                  <p className="font-bold">{waSendStatus.success ? 'Meta Delivery Confirmed' : 'Dispatch Failure'}</p>
                  <p className="mt-0.5">{waSendStatus.message}</p>
                </div>
              )}

              <div className="pt-2 flex justify-end space-x-2">
                <button
                  type="button"
                  onClick={() => setWaSendModalOpen(false)}
                  className="px-3 py-2 rounded-lg bg-slate-800 text-slate-300 font-semibold hover:bg-slate-700"
                >
                  Close
                </button>
                <button
                  type="submit"
                  className="px-4 py-2 rounded-lg bg-emerald-500 hover:bg-emerald-600 text-slate-950 font-bold flex items-center space-x-1"
                >
                  <Send className="w-3.5 h-3.5" />
                  <span>Send via Meta API</span>
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
