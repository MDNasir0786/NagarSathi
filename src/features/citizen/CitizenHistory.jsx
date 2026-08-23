import React, { useEffect, useState } from 'react';
import { Search, Filter, Eye, Download } from 'lucide-react';
import { complaintService } from '../../services';
import { DataTable } from '../../components/ui/DataTable';
import { StatusBadge } from '../../components/ui/StatusBadge';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { Modal } from '../../components/ui/Modal';
import { Button } from '../../components/ui/Button';
import { LoadingSkeleton } from '../../components/feedback/LoadingSkeleton';

export default function CitizenHistory() {
  const [complaints, setComplaints] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [statusFilter, setStatusFilter] = useState('ALL');
  const [priorityFilter, setPriorityFilter] = useState('ALL');
  const [activeModalComplaint, setActiveModalComplaint] = useState(null);

  useEffect(() => {
    complaintService.getComplaints().then((data) => {
      setComplaints(data);
      setLoading(false);
    });
  }, []);

  const filteredData = complaints.filter((c) => {
    const matchesSearch =
      c.title.toLowerCase().includes(search.toLowerCase()) ||
      c.id.toLowerCase().includes(search.toLowerCase()) ||
      c.location.ward.toLowerCase().includes(search.toLowerCase());

    const matchesStatus = statusFilter === 'ALL' || c.status === statusFilter;
    const matchesPriority = priorityFilter === 'ALL' || c.priority === priorityFilter;

    return matchesSearch && matchesStatus && matchesPriority;
  });

  const columns = [
    {
      header: 'Complaint ID',
      accessorKey: 'id',
      cell: (row) => (
        <span className="font-bold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded text-xs border border-emerald-200">
          {row.id}
        </span>
      ),
    },
    {
      header: 'Issue Title',
      accessorKey: 'title',
      cell: (row) => <span className="font-semibold text-gray-900 line-clamp-1">{row.title}</span>,
    },
    {
      header: 'Category',
      accessorKey: 'category',
    },
    {
      header: 'Ward',
      cell: (row) => row.location.ward,
    },
    {
      header: 'Priority',
      cell: (row) => <PriorityBadge priority={row.priority} />,
    },
    {
      header: 'Status',
      cell: (row) => <StatusBadge status={row.status} />,
    },
    {
      header: 'Action',
      cell: (row) => (
        <Button
          size="sm"
          variant="outline"
          onClick={() => setActiveModalComplaint(row)}
          leftIcon={<Eye className="w-3.5 h-3.5" />}
        >
          View
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Complaint History & Archive</h2>
          <p className="text-xs text-gray-500">Filter, search, and export your civic participation record</p>
        </div>

        <Button variant="outline" size="sm" leftIcon={<Download className="w-4 h-4" />}>
          Export History CSV
        </Button>
      </div>

      {/* Filter Bar */}
      <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs grid grid-cols-1 sm:grid-cols-3 gap-3">
        <div className="relative">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search title, ID, ward..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          />
        </div>

        <div>
          <select
            value={statusFilter}
            onChange={(e) => setStatusFilter(e.target.value)}
            className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          >
            <option value="ALL">All Statuses</option>
            <option value="Submitted">Submitted</option>
            <option value="In Progress">In Progress</option>
            <option value="Completed">Completed</option>
            <option value="Verified">Verified</option>
            <option value="Escalated">Escalated</option>
          </select>
        </div>

        <div>
          <select
            value={priorityFilter}
            onChange={(e) => setPriorityFilter(e.target.value)}
            className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
          >
            <option value="ALL">All Priorities</option>
            <option value="CRITICAL">CRITICAL</option>
            <option value="HIGH">HIGH</option>
            <option value="MEDIUM">MEDIUM</option>
            <option value="LOW">LOW</option>
          </select>
        </div>
      </div>

      {/* Data Table */}
      {loading ? (
        <LoadingSkeleton count={4} />
      ) : (
        <DataTable
          columns={columns}
          data={filteredData}
          keyExtractor={(row) => row.id}
          emptyMessage="No complaints match your filters."
        />
      )}

      {/* Complaint Detail Modal */}
      {activeModalComplaint && (
        <Modal
          isOpen={!!activeModalComplaint}
          onClose={() => setActiveModalComplaint(null)}
          title={`Complaint Details - ${activeModalComplaint.id}`}
        >
          <div className="space-y-4 text-xs">
            <div>
              <h4 className="font-bold text-sm text-gray-900 mb-1">{activeModalComplaint.title}</h4>
              <p className="text-gray-600 leading-relaxed">{activeModalComplaint.description}</p>
            </div>

            <div className="grid grid-cols-2 gap-3 bg-gray-50 p-3 rounded-xl border border-gray-100">
              <div>
                <span className="text-[10px] text-gray-400 font-semibold block uppercase">Ward</span>
                <span className="font-bold text-gray-800">{activeModalComplaint.location.ward}</span>
              </div>
              <div>
                <span className="text-[10px] text-gray-400 font-semibold block uppercase">Category</span>
                <span className="font-bold text-gray-800">{activeModalComplaint.category}</span>
              </div>
              <div>
                <span className="text-[10px] text-gray-400 font-semibold block uppercase">Status</span>
                <StatusBadge status={activeModalComplaint.status} />
              </div>
              <div>
                <span className="text-[10px] text-gray-400 font-semibold block uppercase">Priority</span>
                <PriorityBadge priority={activeModalComplaint.priority} />
              </div>
            </div>

            {activeModalComplaint.images?.length > 0 && (
              <div>
                <h5 className="font-bold text-gray-700 mb-2">Attached Photo Evidence</h5>
                <div className="grid grid-cols-3 gap-2">
                  {activeModalComplaint.images.map((img, i) => (
                    <img key={i} src={img} alt="Evidence" className="w-full aspect-video object-cover rounded-lg border border-gray-200" />
                  ))}
                </div>
              </div>
            )}
          </div>
        </Modal>
      )}
    </div>
  );
}
