import React, { useEffect, useState } from 'react';
import { UserCheck, Users, Send, CheckCircle2, MapPin } from 'lucide-react';
import { complaintService } from '../../services';
import { useAuthStore } from '../../stores/authStore';
import { Button } from '../../components/ui/Button';
import { StatusBadge } from '../../components/ui/StatusBadge';

const FIELD_WORKERS = [
  { id: 'user-wrk-102', name: 'Vikram Singh', department: 'Roads & Asphalt Wing', phone: '+91 94250 67890', activeTasks: 2, status: 'AVAILABLE' },
  { id: 'user-wrk-103', name: 'Ramesh Patel', department: 'Electrical & Lighting Cell', phone: '+91 98261 44556', activeTasks: 1, status: 'AVAILABLE' },
  { id: 'user-wrk-104', name: 'Sanjay Kumar', department: 'Jal Nigam & Hydraulics', phone: '+91 99264 55667', activeTasks: 3, status: 'BUSY' },
];

export default function NodalAssignments() {
  const { user } = useAuthStore();
  const [complaints, setComplaints] = useState([]);
  const [selectedComplaintId, setSelectedComplaintId] = useState('');
  const [selectedWorkerId, setSelectedWorkerId] = useState('user-wrk-102');
  const [instructions, setInstructions] = useState('');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    complaintService.getComplaints().then((data) => {
      setComplaints(data);
      if (data.length > 0) setSelectedComplaintId(data[0].id);
    });
  }, []);

  const handleAssignWorker = async (e) => {
    e.preventDefault();
    if (!selectedComplaintId) return;

    const worker = FIELD_WORKERS.find((w) => w.id === selectedWorkerId);
    setSubmitting(true);

    await complaintService.updateComplaintStatus(
      selectedComplaintId,
      'Assigned',
      { name: user?.name || 'Er. Sunita Verma', role: 'NODAL_OFFICER' },
      `Assigned to worker ${worker?.name} (${worker?.department}). Instructions: ${instructions || 'Standard repair dispatch.'}`,
      {
        assignedWorkerId: worker?.id,
        assignedWorkerName: worker?.name,
        assignedWorkerPhone: worker?.phone,
        assignedDepartment: worker?.department,
      }
    );

    setSubmitting(false);
    alert(`Task successfully assigned to ${worker?.name}! Synced with Worker Dashboard.`);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">Field Worker Dispatch Desk</h2>
        <p className="text-xs text-gray-500">Assign unallocated complaints to available ward field staff</p>
      </div>

      <form onSubmit={handleAssignWorker} className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">Select Complaint</label>
          <select
            value={selectedComplaintId}
            onChange={(e) => setSelectedComplaintId(e.target.value)}
            className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:outline-none"
          >
            {complaints.map((c) => (
              <option key={c.id} value={c.id}>
                {c.id} - {c.title} ({c.location.ward})
              </option>
            ))}
          </select>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-2">Select Field Worker</label>
          <div className="grid grid-cols-1 sm:grid-cols-3 gap-3">
            {FIELD_WORKERS.map((w) => (
              <div
                key={w.id}
                onClick={() => setSelectedWorkerId(w.id)}
                className={`p-3.5 rounded-xl border cursor-pointer transition-all ${
                  selectedWorkerId === w.id ? 'bg-purple-50 border-purple-500 shadow-xs' : 'bg-gray-50/50 border-gray-200'
                }`}
              >
                <div className="flex items-center justify-between">
                  <h4 className="font-bold text-xs text-gray-900">{w.name}</h4>
                  <span className="text-[10px] bg-emerald-100 text-emerald-800 font-bold px-1.5 py-0.5 rounded">
                    {w.status}
                  </span>
                </div>
                <p className="text-[11px] text-gray-500 mt-1">{w.department}</p>
                <p className="text-[10px] text-gray-400 mt-0.5">Active Queue: {w.activeTasks} tasks</p>
              </div>
            ))}
          </div>
        </div>

        <div>
          <label className="block text-xs font-semibold text-gray-700 mb-1">Dispatch Instructions & Target Due Date</label>
          <textarea
            rows={3}
            placeholder="Deploy cold-mix asphalt patch team. Ensure compaction and safety cone layout..."
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-purple-500 focus:outline-none"
          />
        </div>

        <div className="pt-2 flex justify-end">
          <Button type="submit" isLoading={submitting} leftIcon={<Send className="w-4 h-4" />}>
            Dispatch Worker Task
          </Button>
        </div>
      </form>
    </div>
  );
}
