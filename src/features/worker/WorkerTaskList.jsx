import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, MapPin, Calendar, Wrench, ArrowRight } from 'lucide-react';
import { taskService } from '../../services';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { Button } from '../../components/ui/Button';

export default function WorkerTaskList() {
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);
  const [filter, setFilter] = useState('ALL');

  useEffect(() => {
    taskService.getWorkerTasks().then(setTasks);
  }, []);

  const filteredTasks = tasks.filter((t) => {
    if (filter === 'PENDING') return t.status === 'PENDING';
    if (filter === 'IN_PROGRESS') return t.status === 'IN_PROGRESS';
    if (filter === 'COMPLETED') return t.status === 'VERIFIED' || t.status === 'COMPLETED_AWAITING_VERIFICATION';
    return true;
  });

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Assigned Field Tasks</h2>
          <p className="text-xs text-gray-500">Touch-friendly task queue for field technicians</p>
        </div>

        <div className="flex items-center gap-1 bg-gray-100 p-1 rounded-xl text-xs font-semibold">
          <button
            onClick={() => setFilter('ALL')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${filter === 'ALL' ? 'bg-white shadow-xs text-gray-900 font-bold' : 'text-gray-600'}`}
          >
            All
          </button>
          <button
            onClick={() => setFilter('PENDING')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${filter === 'PENDING' ? 'bg-white shadow-xs text-gray-900 font-bold' : 'text-gray-600'}`}
          >
            Pending
          </button>
          <button
            onClick={() => setFilter('IN_PROGRESS')}
            className={`px-3 py-1.5 rounded-lg transition-colors ${filter === 'IN_PROGRESS' ? 'bg-white shadow-xs text-gray-900 font-bold' : 'text-gray-600'}`}
          >
            In Progress
          </button>
        </div>
      </div>

      <div className="space-y-4">
        {filteredTasks.map((task) => (
          <div
            key={task.id}
            className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs hover:border-blue-500 transition-all flex flex-col md:flex-row items-start md:items-center justify-between gap-4"
          >
            <div className="space-y-2 flex-1">
              <div className="flex items-center gap-2">
                <span className="text-xs font-bold text-blue-800 bg-blue-50 px-2.5 py-0.5 rounded border border-blue-200">
                  {task.id}
                </span>
                <PriorityBadge priority={task.priority} />
                <span className="text-xs font-semibold text-emerald-800 bg-emerald-50 px-2 py-0.5 rounded">
                  {task.status.replace('_', ' ')}
                </span>
              </div>
              <h3 className="font-bold text-gray-900 text-base">{task.title}</h3>
              <p className="text-xs text-gray-600 line-clamp-2">{task.instructions}</p>
              <div className="flex flex-wrap items-center gap-4 text-xs text-gray-500 pt-1">
                <span className="flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-blue-600" />
                  {task.location.address}
                </span>
                <span className="flex items-center gap-1">
                  <Calendar className="w-3.5 h-3.5 text-blue-600" />
                  Due: {task.scheduledDate}
                </span>
              </div>
            </div>

            <Button
              onClick={() => navigate(`/worker/tasks/${task.id}`)}
              size="md"
              rightIcon={<ArrowRight className="w-4 h-4" />}
            >
              Open Task Controls
            </Button>
          </div>
        ))}
      </div>
    </div>
  );
}
