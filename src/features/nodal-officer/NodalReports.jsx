import React from 'react';
import { BarChart3, FileSpreadsheet, Download } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export default function NodalReports() {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Ward Operations & Resolution Reports</h2>
          <p className="text-xs text-gray-500">Generate SLA performance and department efficiency audits</p>
        </div>
        <Button size="sm" leftIcon={<Download className="w-4 h-4" />}>
          Export PDF Summary
        </Button>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
          <h3 className="font-bold text-gray-900 text-sm mb-2">Monthly Resolution SLA Compliance</h3>
          <p className="text-xs text-emerald-700 font-bold text-2xl">92.4%</p>
          <p className="text-xs text-gray-500 mt-1">Target SLA: 90.0% • 1.2% higher than municipal average</p>
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl p-5 shadow-xs">
          <h3 className="font-bold text-gray-900 text-sm mb-2">Average Resolution Time</h3>
          <p className="text-xs text-blue-700 font-bold text-2xl">24.5 Hours</p>
          <p className="text-xs text-gray-500 mt-1">Average time from Nodal Verification to Field Closure</p>
        </div>
      </div>
    </div>
  );
}
