import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { ShieldAlert, BarChart3, AlertTriangle, CheckCircle2, Clock, Users, ArrowRight, Download } from 'lucide-react';
import { analyticsService } from '../../services';
import { useAuthStore } from '../../stores/authStore';
import { StatCard } from '../../components/ui/StatCard';
import { TrendsChart } from '../../components/charts/TrendsChart';
import { StatusDonutChart } from '../../components/charts/StatusDonutChart';
import { WardBarChart } from '../../components/charts/WardBarChart';
import { Button } from '../../components/ui/Button';
import { LoadingSkeleton } from '../../components/feedback/LoadingSkeleton';

export default function HigherAuthorityDashboard() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsService.getSummary().then((res) => {
      setData(res);
      setLoading(false);
    });
  }, []);

  if (loading || !data) return <LoadingSkeleton count={4} />;

  return (
    <div className="space-y-6">
      {/* Executive Header */}
      <div className="bg-gradient-to-r from-slate-900 via-emerald-950 to-slate-900 text-white rounded-3xl p-6 sm:p-8 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="bg-emerald-500/20 text-emerald-300 border border-emerald-400/30 text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            Bhopal Municipal Corporation • IAS Executive Command
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold mt-2">{user?.name || 'Dr. Ananya Mishra, IAS'}</h1>
          <p className="text-xs sm:text-sm text-slate-300 mt-1">
            City-wide Governance Intelligence, Ward Heatmaps & SLA Escalation Control
          </p>
        </div>

        <div className="flex items-center gap-2">
          <Button onClick={() => navigate('/authority/escalations')} variant="danger" size="sm" leftIcon={<AlertTriangle className="w-4 h-4" />}>
            Escalation Desk ({data.escalatedComplaints})
          </Button>
          <Button onClick={() => navigate('/authority/analytics')} size="sm" leftIcon={<BarChart3 className="w-4 h-4" />}>
            City Analytics
          </Button>
        </div>
      </div>

      {/* City-wide KPI Cards */}
      <div className="grid grid-cols-2 lg:grid-cols-5 gap-3 sm:gap-4">
        <StatCard title="Total Reported" value={data.totalComplaints} icon={<BarChart3 className="w-5 h-5 text-blue-600" />} />
        <StatCard title="Active Issues" value={data.activeComplaints} icon={<Clock className="w-5 h-5 text-indigo-600" />} iconBgColor="bg-indigo-50" />
        <StatCard title="Resolved" value={data.resolvedComplaints} icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />} iconBgColor="bg-emerald-50" />
        <StatCard title="SLA Escalations" value={data.escalatedComplaints} icon={<AlertTriangle className="w-5 h-5 text-red-600" />} iconBgColor="bg-red-50" />
        <StatCard title="Satisfaction" value={`${data.citizenSatisfactionRate}%`} icon={<Users className="w-5 h-5 text-purple-600" />} iconBgColor="bg-purple-50" className="col-span-2 sm:col-span-1" />
      </div>

      {/* Charts Grid */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <div className="lg:col-span-2 bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-3">
          <div className="flex items-center justify-between">
            <h3 className="font-bold text-gray-900 text-sm">Monthly Complaint Trends & Resolution Rate</h3>
            <span className="text-xs text-gray-400">2026 Monsoon Quarter</span>
          </div>
          <TrendsChart data={data.monthlyTrends} />
        </div>

        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-3">
          <h3 className="font-bold text-gray-900 text-sm">Issue Category Breakdown</h3>
          <StatusDonutChart data={data.categoryBreakdown} />
        </div>
      </div>

      {/* Ward Performance Bar Chart */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-3">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900 text-sm">Ward-wise Resolution Performance</h3>
          <span className="text-xs text-emerald-700 font-semibold">Average SLA: {data.avgResolutionTimeHours} Hours</span>
        </div>
        <WardBarChart data={data.wardPerformance} />
      </div>
    </div>
  );
}
