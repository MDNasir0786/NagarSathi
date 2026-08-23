import React, { useEffect, useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { Search, MapPin, Calendar, User, Wrench, ShieldCheck, CheckCircle2, Clock } from 'lucide-react';
import { complaintService } from '../../services';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { Timeline } from '../../components/ui/Timeline';
import { MapView } from '../../components/maps/MapView';
import { AIInsightCard } from '../../components/ai/AIInsightCard';
import { LoadingSkeleton } from '../../components/feedback/LoadingSkeleton';

export default function ComplaintTracking() {
  const [searchParams] = useSearchParams();
  const initialId = searchParams.get('id');

  const [complaints, setComplaints] = useState([]);
  const [selectedComplaint, setSelectedComplaint] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    complaintService.getComplaints().then((data) => {
      setComplaints(data);
      if (initialId) {
        const found = data.find((c) => c.id === initialId);
        if (found) setSelectedComplaint(found);
        else if (data.length > 0) setSelectedComplaint(data[0]);
      } else if (data.length > 0) {
        setSelectedComplaint(data[0]);
      }
      setLoading(false);
    });
  }, [initialId]);

  const filtered = complaints.filter(
    (c) =>
      c.id.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.title.toLowerCase().includes(searchQuery.toLowerCase()) ||
      c.location.ward.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="space-y-6">
      {/* Header & Search */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Complaint Tracking & Resolution Timeline</h2>
          <p className="text-xs text-gray-500">Real-time status updates and geotagged execution proof</p>
        </div>

        <div className="relative w-full sm:w-72">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search Complaint ID or Keyword..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          />
        </div>
      </div>

      {loading ? (
        <LoadingSkeleton count={3} />
      ) : (
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
          {/* Complaint Selector Sidebar */}
          <div className="space-y-3">
            <h3 className="text-xs font-bold uppercase tracking-wider text-gray-400 px-1">
              Your Complaints ({filtered.length})
            </h3>
            {filtered.map((item) => (
              <div
                key={item.id}
                onClick={() => setSelectedComplaint(item)}
                className={`p-4 rounded-2xl border transition-all cursor-pointer ${
                  selectedComplaint?.id === item.id
                    ? 'bg-emerald-50/70 border-emerald-500 shadow-sm'
                    : 'bg-white border-gray-200 hover:border-emerald-300'
                }`}
              >
                <div className="flex items-center justify-between gap-2 mb-1.5">
                  <span className="text-xs font-bold text-emerald-800 bg-white px-2 py-0.5 rounded border border-emerald-200">
                    {item.id}
                  </span>
                  <StatusBadge status={item.status} />
                </div>
                <h4 className="font-bold text-gray-900 text-xs line-clamp-1 mb-1">{item.title}</h4>
                <div className="flex items-center justify-between text-[11px] text-gray-500">
                  <span>{item.location.ward}</span>
                  <PriorityBadge priority={item.priority} />
                </div>
              </div>
            ))}
          </div>

          {/* Complaint Detail & Timeline View */}
          {selectedComplaint ? (
            <div className="lg:col-span-2 space-y-6">
              {/* Complaint Header */}
              <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-gray-100 pb-4">
                  <div>
                    <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded-md border border-emerald-200">
                      ID: {selectedComplaint.id}
                    </span>
                    <h3 className="text-lg font-bold text-gray-900 mt-2">{selectedComplaint.title}</h3>
                  </div>
                  <div className="flex items-center gap-2">
                    <PriorityBadge priority={selectedComplaint.priority} />
                    <StatusBadge status={selectedComplaint.status} />
                  </div>
                </div>

                <p className="text-xs text-gray-600 leading-relaxed">{selectedComplaint.description}</p>

                <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 text-xs bg-gray-50 p-3 rounded-xl border border-gray-100">
                  <div className="flex items-center gap-2">
                    <MapPin className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>{selectedComplaint.location.address}</span>
                  </div>
                  <div className="flex items-center gap-2">
                    <Calendar className="w-4 h-4 text-emerald-600 shrink-0" />
                    <span>Reported: {new Date(selectedComplaint.createdAt).toLocaleDateString()}</span>
                  </div>
                  {selectedComplaint.assignedWorkerName && (
                    <div className="flex items-center gap-2 sm:col-span-2">
                      <Wrench className="w-4 h-4 text-emerald-600 shrink-0" />
                      <span>
                        Assigned Worker: <strong className="text-gray-900">{selectedComplaint.assignedWorkerName}</strong> ({selectedComplaint.assignedDepartment})
                      </span>
                    </div>
                  )}
                </div>

                {/* Images Preview */}
                {selectedComplaint.images?.length > 0 && (
                  <div>
                    <h4 className="text-xs font-bold text-gray-700 mb-2">Citizen Uploaded Evidence</h4>
                    <div className="grid grid-cols-3 gap-2">
                      {selectedComplaint.images.map((img, i) => (
                        <img
                          key={i}
                          src={img}
                          alt="Citizen evidence"
                          className="w-full aspect-video object-cover rounded-lg border border-gray-200"
                        />
                      ))}
                    </div>
                  </div>
                )}
              </div>

              {/* AI Verification Section */}
              {selectedComplaint.aiAnalysis && <AIInsightCard aiAnalysis={selectedComplaint.aiAnalysis} />}

              {/* Resolution Proof Comparison (If completed) */}
              {selectedComplaint.resolutionProof && (
                <div className="bg-emerald-50/60 border border-emerald-200 rounded-2xl p-6 space-y-3">
                  <div className="flex items-center gap-2 text-emerald-900 font-bold text-sm">
                    <CheckCircle2 className="w-5 h-5 text-emerald-600" />
                    Field Completion Evidence & Work Verification
                  </div>
                  <p className="text-xs text-emerald-800">{selectedComplaint.resolutionProof.notes}</p>
                  {selectedComplaint.resolutionProof.images?.length > 0 && (
                    <div className="grid grid-cols-2 sm:grid-cols-3 gap-2 pt-2">
                      {selectedComplaint.resolutionProof.images.map((img, i) => (
                        <img
                          key={i}
                          src={img}
                          alt="Resolution proof"
                          className="w-full aspect-video object-cover rounded-lg border border-emerald-300"
                        />
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* Visual Map Location */}
              <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
                <h4 className="text-xs font-bold text-gray-700 mb-3">GIS Geotagged Location Map</h4>
                <MapView
                  center={[selectedComplaint.location.lat, selectedComplaint.location.lng]}
                  zoom={14}
                  height="220px"
                  markers={[selectedComplaint]}
                />
              </div>

              {/* Lifecycle Visual Timeline */}
              <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
                <h4 className="text-sm font-bold text-gray-900 mb-4">Step-by-Step Resolution Timeline</h4>
                <Timeline events={selectedComplaint.timeline || []} />
              </div>
            </div>
          ) : (
            <div className="lg:col-span-2 bg-white border border-gray-200 rounded-2xl p-8 text-center text-xs text-gray-400">
              Select a complaint from the left panel to inspect timeline.
            </div>
          )}
        </div>
      )}
    </div>
  );
}
