import React, { useEffect, useState } from 'react';
import { ShieldAlert, AlertTriangle, CheckCircle2, UserCheck } from 'lucide-react';
import { complaintService } from '../../services';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { Button } from '../../components/ui/Button';

export default function AuthorityEscalations() {
  const [escalated, setEscalated] = useState([]);

  useEffect(() => {
    complaintService.getComplaints().then((data) => {
      setEscalated(data.filter((c) => c.isEscalated || c.status === 'Escalated'));
    });
  }, []);

  const handleIntervene = (id) => {
    alert(`Commissioner Executive Intervention order issued for Complaint ${id}! Dispatched to Nodal Head.`);
  };

  return (
    <div className="space-y-6">
      <div className="bg-red-50 border border-red-200 rounded-2xl p-6 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-red-900 flex items-center gap-2">
            <AlertTriangle className="w-6 h-6 text-red-600" />
            Commissioner SLA Escalation Desk
          </h2>
          <p className="text-xs text-red-700 mt-1">High severity issues exceeding maximum resolution SLA</p>
        </div>
      </div>

      <div className="space-y-4">
        {escalated.map((c) => (
          <div key={c.id} className="bg-white border border-red-200 rounded-2xl p-6 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-red-800 bg-red-50 px-2.5 py-1 rounded border border-red-200">
                {c.id}
              </span>
              <PriorityBadge priority={c.priority} />
            </div>

            <h3 className="font-bold text-gray-900 text-sm">{c.title}</h3>
            <p className="text-xs text-red-800 bg-red-50/70 p-3 rounded-xl border border-red-100 font-medium">
              Reason: {c.escalationReason || 'Resolution SLA exceeded by 48h without worker progress update.'}
            </p>

            <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
              <span>Ward: {c.location.ward}</span>
              <Button size="sm" variant="danger" onClick={() => handleIntervene(c.id)}>
                Issue Executive Order
              </Button>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
