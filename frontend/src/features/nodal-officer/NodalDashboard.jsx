import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Shield, FileText, Users, AlertTriangle, CheckCircle2, ArrowRight, Clock } from 'lucide-react';
import { complaintService } from '../../services';
import { useAuthStore } from '../../stores/authStore';
import { StatCard } from '../../components/ui/StatCard';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { Button } from '../../components/ui/Button';

export default function NodalDashboard() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);

  useEffect(() => {
    complaintService.getComplaints().then(setComplaints);
  }, []);

  const pendingVerification = complaints.filter((c) => c.status === 'Submitted' || c.status === 'In Review').length;
  const assigned = complaints.filter((c) => c.status === 'Assigned' || c.status === 'In Progress').length;
  const escalated = complaints.filter((c) => c.isEscalated || c.status === 'Escalated').length;
  const completed = complaints.filter((c) => c.status === 'Completed' || c.status === 'Verified').length;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-purple-700 to-indigo-800 text-white rounded-3xl p-6 sm:p-8 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="bg-white/20 text-white text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            Nodal Operations Control
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold mt-2">{user?.name}</h1>
          <p className="text-xs sm:text-sm text-purple-100 mt-1">
            {user?.ward || 'Zone 8 (Wards 42-49)'} • Municipal Operations Command
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={() => navigate('/nodal/requests')}
            className="bg-white text-purple-900 hover:bg-purple-50 font-bold"
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            Verification Desk ({pendingVerification})
          </Button>
          <Button
            onClick={() => navigate('/nodal/assignments')}
            variant="outline"
            className="bg-purple-900/40 text-white border-purple-400 hover:bg-purple-900/60"
          >
            Dispatch Worker
          </Button>
        </div>
      </div>

      {/* Stats KPI */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Pending Review" value={pendingVerification} icon={<Clock className="w-5 h-5 text-purple-600" />} iconBgColor="bg-purple-50" />
        <StatCard title="Dispatched" value={assigned} icon={<Users className="w-5 h-5 text-blue-600" />} iconBgColor="bg-blue-50" />
        <StatCard title="Escalations" value={escalated} icon={<AlertTriangle className="w-5 h-5 text-red-600" />} iconBgColor="bg-red-50" />
        <StatCard title="Verified Work" value={completed} icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />} iconBgColor="bg-emerald-50" />
      </div>

      {/* Pending Inspection Stream */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900 text-base">Complaints Awaiting Nodal Inspection</h3>
          <Button variant="ghost" size="sm" onClick={() => navigate('/nodal/requests')}>
            View All Requests
          </Button>
        </div>

        <div className="space-y-3">
          {complaints.slice(0, 3).map((item) => (
            <div
              key={item.id}
              onClick={() => navigate(`/nodal/requests?id=${item.id}`)}
              className="p-4 rounded-2xl border border-gray-200 hover:border-purple-500 bg-gray-50/50 hover:bg-white transition-all cursor-pointer flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-purple-800 bg-purple-50 px-2 py-0.5 rounded border border-purple-200">
                    {item.id}
                  </span>
                  <StatusBadge status={item.status} />
                  <PriorityBadge priority={item.priority} />
                </div>
                <h4 className="font-bold text-gray-900 text-sm">{item.title}</h4>
                <p className="text-xs text-gray-500">{item.location.address} ({item.location.ward})</p>
              </div>

              <Button size="sm" variant="outline">
                Inspect AI Analysis & Assign
              </Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
