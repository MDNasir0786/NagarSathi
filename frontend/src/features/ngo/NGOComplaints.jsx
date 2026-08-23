import React, { useEffect, useState } from 'react';
import { FileText, HeartHandshake, CheckCircle2 } from 'lucide-react';
import { complaintService } from '../../services';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { Button } from '../../components/ui/Button';

export default function NGOComplaints() {
  const [complaints, setComplaints] = useState([]);

  useEffect(() => {
    complaintService.getComplaints().then(setComplaints);
  }, []);

  const handleAdopt = (id) => {
    alert(`NGO successfully adopted complaint ${id} for volunteer resolution drive!`);
  };

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">Community Complaint Adoption Desk</h2>
        <p className="text-xs text-gray-500">Adopt neighborhood civic complaints for volunteer cleanliness and awareness drives</p>
      </div>

      <div className="space-y-4">
        {complaints.map((c) => (
          <div key={c.id} className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
            <div className="space-y-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                  {c.id}
                </span>
                <StatusBadge status={c.status} />
                <PriorityBadge priority={c.priority} />
              </div>
              <h3 className="font-bold text-gray-900 text-sm">{c.title}</h3>
              <p className="text-xs text-gray-500">{c.location.address} ({c.location.ward})</p>
            </div>

            <Button
              size="sm"
              onClick={() => handleAdopt(c.id)}
              leftIcon={<HeartHandshake className="w-4 h-4" />}
            >
              Adopt for NGO Drive
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
