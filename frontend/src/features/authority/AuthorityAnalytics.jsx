import React, { useEffect, useState } from 'react';
import { BarChart3, Filter, Download } from 'lucide-react';
import { analyticsService } from '../../services';
import { TrendsChart } from '../../components/charts/TrendsChart';
import { WardBarChart } from '../../components/charts/WardBarChart';
import { MapView } from '../../components/maps/MapView';
import { Button } from '../../components/ui/Button';

export default function AuthorityAnalytics() {
  const [data, setData] = useState(null);

  useEffect(() => {
    analyticsService.getSummary().then(setData);
  }, []);

  if (!data) return null;

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex items-center justify-between">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Bhopal Civic Analytics & Ward Heatmaps</h2>
          <p className="text-xs text-gray-500">Geospatial issue distribution and municipal SLA compliance reports</p>
        </div>

        <Button size="sm" leftIcon={<Download className="w-4 h-4" />}>
          Export Executive Report
        </Button>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
        <h3 className="text-xs font-bold text-gray-700 mb-3">Geospatial Ward Density Map</h3>
        <MapView height="320px" />
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-3">
          <h3 className="font-bold text-gray-900 text-sm">Monthly Incident Trends</h3>
          <TrendsChart data={data.monthlyTrends} />
        </div>
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-3">
          <h3 className="font-bold text-gray-900 text-sm">Ward Resolution Comparison</h3>
          <WardBarChart data={data.wardPerformance} />
        </div>
      </div>
    </div>
  );
}
