import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { PlusCircle, FileText, Award, CheckCircle2, Clock, MapPin, ArrowRight, Sparkles, Bell } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { complaintService } from '../../services';
import { StatCard } from '../../components/ui/StatCard';
import { ActionCard } from '../../components/ui/ActionCard';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { Button } from '../../components/ui/Button';
import { LoadingSkeleton } from '../../components/feedback/LoadingSkeleton';

export default function CitizenDashboard() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    complaintService.getComplaints().then((data) => {
      setComplaints(data);
      setLoading(false);
    });
  }, []);

  const total = complaints.length;
  const active = complaints.filter((c) => c.status !== 'Completed' && c.status !== 'Verified' && c.status !== 'Closed').length;
  const resolved = complaints.filter((c) => c.status === 'Completed' || c.status === 'Verified' || c.status === 'Closed').length;

  return (
    <div className="space-y-6">
      {/* Welcome Banner */}
      <div className="bg-gradient-to-r from-emerald-600 to-teal-700 text-white rounded-3xl p-6 sm:p-8 shadow-md relative overflow-hidden">
        <div className="relative z-10">
          <span className="bg-white/20 text-white text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            Smart Bhopal Citizen Portal
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold mt-3">Welcome back, {user?.name}!</h1>
          <p className="text-xs sm:text-sm text-emerald-100 mt-1 max-w-xl leading-relaxed">
            Report civic issues in your ward, track AI-verified resolution progress, and earn Green Citizen reward points.
          </p>

          <div className="flex flex-wrap items-center gap-3 mt-6">
            <Button
              onClick={() => navigate('/citizen/complaints/new')}
              variant="secondary"
              size="md"
              leftIcon={<PlusCircle className="w-4 h-4 text-emerald-700" />}
            >
              Register New Complaint
            </Button>
            <Button
              onClick={() => navigate('/citizen/complaints')}
              variant="outline"
              size="md"
              className="bg-emerald-800/40 text-white border-emerald-400 hover:bg-emerald-800/60"
              leftIcon={<FileText className="w-4 h-4" />}
            >
              Track Active Complaints
            </Button>
          </div>
        </div>
      </div>

      {/* KPI Stat Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard
          title="Reward Points"
          value={user?.points || 450}
          subtitle="Tier: Green Champion"
          icon={<Award className="w-5 h-5 text-amber-600" />}
          iconBgColor="bg-amber-50"
        />
        <StatCard
          title="Total Reported"
          value={total}
          subtitle="Registered by you"
          icon={<FileText className="w-5 h-5 text-blue-600" />}
          iconBgColor="bg-blue-50"
        />
        <StatCard
          title="Active Issues"
          value={active}
          subtitle="In review / In progress"
          icon={<Clock className="w-5 h-5 text-indigo-600" />}
          iconBgColor="bg-indigo-50"
        />
        <StatCard
          title="Resolved"
          value={resolved}
          subtitle="Verified by BMC"
          icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />}
          iconBgColor="bg-emerald-50"
        />
      </div>

      {/* Quick Action Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <ActionCard
          title="Register Issue"
          description="Upload geotagged photo with AI auto-categorization & priority prediction."
          icon={<PlusCircle className="w-6 h-6" />}
          onClick={() => navigate('/citizen/complaints/new')}
          badge="AI Powered"
        />
        <ActionCard
          title="Track Progress"
          description="View step-by-step visual timeline, assigned worker details & resolution proof."
          icon={<Clock className="w-6 h-6" />}
          onClick={() => navigate('/citizen/complaints')}
        />
        <ActionCard
          title="Rewards & Badges"
          description="View earned reward points, digital certificates & ward leaderboards."
          icon={<Award className="w-6 h-6" />}
          onClick={() => navigate('/citizen/rewards')}
        />
      </div>

      {/* Active Complaints Stream */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="font-bold text-gray-900 text-base">Your Active Civic Complaints</h3>
            <p className="text-xs text-gray-500">Live progress tracking for reported issues in Bhopal</p>
          </div>
          <Button variant="ghost" size="sm" onClick={() => navigate('/citizen/complaints')}>
            View All ({total})
          </Button>
        </div>

        {loading ? (
          <LoadingSkeleton count={2} />
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {complaints.slice(0, 2).map((item) => (
              <div
                key={item.id}
                onClick={() => navigate(`/citizen/complaints?id=${item.id}`)}
                className="border border-gray-200 hover:border-emerald-500 rounded-xl p-4 transition-all hover:shadow-md cursor-pointer bg-gray-50/40"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
                    {item.id}
                  </span>
                  <StatusBadge status={item.status} />
                </div>
                <h4 className="font-bold text-gray-900 text-sm line-clamp-1 mb-1">{item.title}</h4>
                <p className="text-xs text-gray-500 line-clamp-2 mb-3">{item.description}</p>
                <div className="flex items-center justify-between text-xs text-gray-500 pt-2 border-t border-gray-100">
                  <span className="flex items-center gap-1">
                    <MapPin className="w-3.5 h-3.5 text-emerald-600" />
                    {item.location.ward}
                  </span>
                  <PriorityBadge priority={item.priority} />
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
