import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { CheckCircle2, XCircle, AlertTriangle, ShieldCheck, User, Wrench } from 'lucide-react';
import { complaintService } from '../../services';
import { useAuthStore } from '../../stores/authStore';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { AIInsightCard } from '../../components/ai/AIInsightCard';
import { MapView } from '../../components/maps/MapView';
import { Button } from '../../components/ui/Button';

export default function NodalRequests() {
  const { user } = useAuthStore();
  const [searchParams] = useSearchParams();
  const initialId = searchParams.get('id');

  const [complaints, setComplaints] = useState([]);
  const [selected, setSelected] = useState(null);

  useEffect(() => {
    complaintService.getComplaints().then((data) => {
      setComplaints(data);
      if (initialId) {
        const found = data.find((c) => c.id === initialId);
        if (found) setSelected(found);
        else if (data.length > 0) setSelected(data[0]);
      } else if (data.length > 0) {
        setSelected(data[0]);
      }
    });
  }, [initialId]);

  const handleVerifyAction = async (status, notes) => {
    if (!selected) return;
    const updated = await complaintService.updateComplaintStatus(
      selected.id,
      status,
      { name: user?.name || 'Er. Sunita Verma', role: 'NODAL_OFFICER' },
      notes
    );
    setSelected(updated);
    alert(`Complaint ${selected.id} set to status: ${status}`);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">Complaint Verification Desk</h2>
        <p className="text-xs text-gray-500">Inspect citizen geotagged photos, AI confidence scores & issue validation</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left List */}
        <div className="space-y-3">
          {complaints.map((item) => (
            <div
              key={item.id}
              onClick={() => setSelected(item)}
              className={`p-4 rounded-2xl border cursor-pointer transition-all ${
                selected?.id === item.id ? 'bg-purple-50/70 border-purple-500 shadow-xs' : 'bg-white border-gray-200'
              }`}
            >
              <div className="flex items-center justify-between gap-2 mb-1">
                <span className="text-xs font-bold text-purple-800 bg-white px-2 py-0.5 rounded border border-purple-200">
                  {item.id}
                </span>
                <StatusBadge status={item.status} />
              </div>
              <h4 className="font-bold text-gray-900 text-xs line-clamp-1">{item.title}</h4>
              <p className="text-[11px] text-gray-500 mt-1">{item.location.ward}</p>
            </div>
          ))}
        </div>

        {/* Right Detail */}
        {selected ? (
          <div className="lg:col-span-2 space-y-6">
            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
              <div className="flex items-center justify-between border-b border-gray-100 pb-3">
                <h3 className="font-bold text-base text-gray-900">{selected.title}</h3>
                <PriorityBadge priority={selected.priority} />
              </div>
              <p className="text-xs text-gray-600 leading-relaxed">{selected.description}</p>

              {selected.images?.length > 0 && (
                <div>
                  <h4 className="text-xs font-bold text-gray-700 mb-2">Submitted Evidence</h4>
                  <div className="grid grid-cols-3 gap-2">
                    {selected.images.map((img, i) => (
                      <img key={i} src={img} alt="Evidence" className="w-full aspect-video object-cover rounded-lg border border-gray-200" />
                    ))}
                  </div>
                </div>
              )}
            </div>

            {/* AI Engine Results */}
            {selected.aiAnalysis && <AIInsightCard aiAnalysis={selected.aiAnalysis} />}

            {/* Verification Actions */}
            <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
              <h4 className="text-xs font-bold uppercase tracking-wider text-gray-400">Nodal Verification Decisions</h4>
              <div className="flex flex-wrap items-center gap-3">
                <Button
                  onClick={() => handleVerifyAction('In Review', 'Nodal Officer validated issue evidence.')}
                  leftIcon={<CheckCircle2 className="w-4 h-4" />}
                >
                  Verify & Validate Issue
                </Button>
                <Button
                  variant="danger"
                  onClick={() => handleVerifyAction('Escalated', 'Escalated to Higher Authority for immediate SLA intervention.')}
                  leftIcon={<AlertTriangle className="w-4 h-4" />}
                >
                  Escalate to Commissioner
                </Button>
              </div>
            </div>
          </div>
        ) : null}
      </div>
    </div>
  );
}
