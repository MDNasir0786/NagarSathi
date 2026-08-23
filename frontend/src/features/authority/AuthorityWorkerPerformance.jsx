import React, { useEffect, useState } from 'react';
import { UserCheck, Star, Clock } from 'lucide-react';
import { analyticsService } from '../../services';
import { DataTable } from '../../components/ui/DataTable';

export default function AuthorityWorkerPerformance() {
  const [data, setData] = useState(null);

  useEffect(() => {
    analyticsService.getSummary().then(setData);
  }, []);

  if (!data) return null;

  const columns = [
    {
      header: 'Technician Name',
      cell: (row) => <span className="font-bold text-gray-900">{row.name}</span>,
    },
    {
      header: 'Completed Tasks',
      accessorKey: 'completed',
    },
    {
      header: 'Avg Resolution Time',
      cell: (row) => `${row.avgTimeHours} Hours`,
    },
    {
      header: 'Citizen Satisfaction Rating',
      cell: (row) => <span className="font-bold text-emerald-700">★ {row.rating} / 5.0</span>,
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">Field Worker Resolution Efficiency Audit</h2>
        <p className="text-xs text-gray-500">Department resolution speed and citizen satisfaction leaderboards</p>
      </div>

      <DataTable columns={columns} data={data.workerPerformance} keyExtractor={(r) => r.name} />
    </div>
  );
}
