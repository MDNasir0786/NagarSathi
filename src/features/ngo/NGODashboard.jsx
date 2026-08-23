import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { MapPin, Users, Calendar, Award, Plus, ArrowRight } from 'lucide-react';
import { ngoService } from '../../services';
import { useAuthStore } from '../../stores/authStore';
import { StatCard } from '../../components/ui/StatCard';
import { Button } from '../../components/ui/Button';

export default function NGODashboard() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [areas, setAreas] = useState([]);
  const [volunteers, setVolunteers] = useState([]);
  const [events, setEvents] = useState([]);

  useEffect(() => {
    Promise.all([ngoService.getNGOAreas(), ngoService.getVolunteers(), ngoService.getCommunityEvents()]).then(
      ([a, v, e]) => {
        setAreas(a);
        setVolunteers(v);
        setEvents(e);
      }
    );
  }, []);

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-gradient-to-r from-teal-700 to-emerald-800 text-white rounded-3xl p-6 sm:p-8 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="bg-white/20 text-white text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            NGO Community Platform
          </span>
          <h1 className="text-2xl sm:text-3xl font-extrabold mt-2">{user?.organization || 'Green Bhopal Foundation'}</h1>
          <p className="text-xs sm:text-sm text-teal-100 mt-1">Urban Environment & Community Citizen Participation</p>
        </div>

        <div className="flex items-center gap-2">
          <Button
            onClick={() => navigate('/ngo/volunteers')}
            className="bg-white text-teal-900 hover:bg-teal-50 font-bold"
            rightIcon={<Plus className="w-4 h-4" />}
          >
            Add New Volunteer
          </Button>
          <Button onClick={() => navigate('/ngo/events')} variant="outline" className="bg-teal-900/40 text-white border-teal-400">
            Create Drive
          </Button>
        </div>
      </div>

      {/* KPI Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Assigned Wards" value={areas.length} icon={<MapPin className="w-5 h-5 text-teal-600" />} iconBgColor="bg-teal-50" />
        <StatCard title="Active Volunteers" value={volunteers.length} icon={<Users className="w-5 h-5 text-emerald-600" />} iconBgColor="bg-emerald-50" />
        <StatCard title="Upcoming Drives" value={events.length} icon={<Calendar className="w-5 h-5 text-blue-600" />} iconBgColor="bg-blue-50" />
        <StatCard title="Community Points" value="1,420" icon={<Award className="w-5 h-5 text-amber-600" />} iconBgColor="bg-amber-50" />
      </div>

      {/* Assigned Areas List */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900 text-base">Assigned Ward Coverage Areas</h3>
          <Button variant="ghost" size="sm" onClick={() => navigate('/ngo/areas')}>
            View All Areas
          </Button>
        </div>

        <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
          {areas.map((a) => (
            <div key={a.id} className="p-4 rounded-2xl border border-gray-200 bg-gray-50/50 space-y-2">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-teal-800 bg-teal-50 px-2 py-0.5 rounded border border-teal-200">
                  {a.wardNumber}
                </span>
                <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                  {a.coverageStatus}
                </span>
              </div>
              <h4 className="font-bold text-gray-900 text-xs">{a.wardName}</h4>
              <div className="text-[11px] text-gray-500 space-y-0.5 pt-1 border-t border-gray-100">
                <p>Active Issues: {a.activeComplaintsCount}</p>
                <p>Volunteers Deployed: {a.volunteersCount}</p>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
