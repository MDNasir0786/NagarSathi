import React, { useEffect, useState } from 'react';
import { Calendar, Users, MapPin, Plus } from 'lucide-react';
import { ngoService } from '../../services';
import { Button } from '../../components/ui/Button';

export default function NGOEvents() {
  const [events, setEvents] = useState([]);

  useEffect(() => {
    ngoService.getCommunityEvents().then(setEvents);
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Community Drives & Civic Events</h2>
          <p className="text-xs text-gray-500">Organize cleanliness drives, sapling plantations & awareness campaigns</p>
        </div>

        <Button leftIcon={<Plus className="w-4 h-4" />}>Create New Drive</Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {events.map((e) => (
          <div key={e.id} className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-teal-800 bg-teal-50 px-2.5 py-0.5 rounded border border-teal-200">
                {e.type}
              </span>
              <span className="text-[10px] font-bold text-blue-700 bg-blue-100 px-2 py-0.5 rounded-full">
                {e.status}
              </span>
            </div>
            <h3 className="font-bold text-gray-900 text-sm">{e.title}</h3>
            <div className="space-y-1 text-xs text-gray-600 bg-gray-50 p-3 rounded-xl border border-gray-100">
              <p className="flex items-center gap-1.5"><MapPin className="w-3.5 h-3.5 text-teal-600" /> {e.location}</p>
              <p className="flex items-center gap-1.5"><Calendar className="w-3.5 h-3.5 text-teal-600" /> {e.date} • {e.time}</p>
              <p className="flex items-center gap-1.5"><Users className="w-3.5 h-3.5 text-teal-600" /> {e.volunteersEnrolled} / {e.targetVolunteers} Volunteers Enrolled</p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
