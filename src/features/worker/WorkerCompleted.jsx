import React, { useEffect, useState } from 'react';
import { CheckCircle2, Calendar, MapPin } from 'lucide-react';
import { taskService } from '../../services';
import { StatusBadge } from '../../components/ui/StatusBadge';

export default function WorkerCompleted() {
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    taskService.getWorkerTasks().then((data) => {
      setTasks(data.filter((t) => t.status === 'VERIFIED' || t.status === 'COMPLETED_AWAITING_VERIFICATION'));
    });
  }, []);

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">Completed & Verified Work History</h2>
        <p className="text-xs text-gray-500">Archive of resolved civic infrastructure assignments</p>
      </div>

      <div className="space-y-4">
        {tasks.length === 0 ? (
          <div className="bg-white border border-gray-200 rounded-2xl p-8 text-center text-xs text-gray-400">
            No completed tasks yet.
          </div>
        ) : (
          tasks.map((t) => (
            <div key={t.id} className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-3">
              <div className="flex items-center justify-between">
                <span className="text-xs font-bold text-emerald-800 bg-emerald-50 px-2.5 py-1 rounded border border-emerald-200">
                  {t.id}
                </span>
                <StatusBadge status={t.status === 'VERIFIED' ? 'Verified' : 'Completed'} />
              </div>
              <h3 className="font-bold text-gray-900 text-sm">{t.title}</h3>
              <p className="text-xs text-gray-600 bg-gray-50 p-2.5 rounded-xl border border-gray-100">{t.workerNotes}</p>
              
              {t.afterImages?.length > 0 && (
                <div className="grid grid-cols-3 gap-2 pt-1">
                  {t.afterImages.map((img, i) => (
                    <img key={i} src={img} alt="Resolution proof" className="w-full aspect-video object-cover rounded-lg border border-emerald-200" />
                  ))}
                </div>
              )}
            </div>
          ))
        )}
      </div>
    </div>
  );
}
