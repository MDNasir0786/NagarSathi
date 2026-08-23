import React, { useEffect, useState } from 'react';
import { MapPin, Users, CheckCircle2 } from 'lucide-react';
import { ngoService } from '../../services';
import { MapView } from '../../components/maps/MapView';

export default function NGOAreas() {
  const [areas, setAreas] = useState([]);

  useEffect(() => {
    ngoService.getNGOAreas().then(setAreas);
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">NGO Assigned Ward Coverage</h2>
        <p className="text-xs text-gray-500">Monitor ward community resolution progress and volunteer density</p>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
        <h3 className="text-xs font-bold text-gray-700 mb-3">Ward Boundaries & Active Issue GIS Map</h3>
        <MapView height="300px" />
      </div>

      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {areas.map((a) => (
          <div key={a.id} className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs space-y-3">
            <div className="flex items-center justify-between">
              <span className="text-xs font-bold text-teal-800 bg-teal-50 px-2.5 py-1 rounded border border-teal-200">
                {a.wardNumber}
              </span>
              <span className="text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                {a.coverageStatus}
              </span>
            </div>
            <h3 className="font-bold text-gray-900 text-sm">{a.wardName}</h3>
            <div className="space-y-1 text-xs text-gray-600 bg-gray-50 p-3 rounded-xl border border-gray-100">
              <p>Active Ward Issues: <strong className="text-gray-900">{a.activeComplaintsCount}</strong></p>
              <p>Resolved by NGO: <strong className="text-emerald-700">{a.resolvedComplaintsCount}</strong></p>
              <p>Active Volunteers: <strong className="text-teal-700">{a.volunteersCount}</strong></p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
