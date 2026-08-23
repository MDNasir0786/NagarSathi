import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { CheckSquare, Clock, CheckCircle2, Award, MapPin, ArrowRight, Bell } from 'lucide-react';
import { taskService } from '../../services';
import { useAuthStore } from '../../stores/authStore';
import { StatCard } from '../../components/ui/StatCard';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { Button } from '../../components/ui/Button';

export default function WorkerDashboard() {
  const { user } = useAuthStore();
  const navigate = useNavigate();
  const [tasks, setTasks] = useState([]);

  useEffect(() => {
    taskService.getWorkerTasks().then(setTasks);
  }, []);

  const total = tasks.length;
  const pending = tasks.filter((t) => t.status === 'PENDING').length;
  const inProgress = tasks.filter((t) => t.status === 'IN_PROGRESS').length;
  const completed = tasks.filter((t) => t.status === 'VERIFIED' || t.status === 'COMPLETED_AWAITING_VERIFICATION').length;

  return (
    <div className="space-y-6">
      {/* Header Banner */}
      <div className="bg-gradient-to-r from-blue-700 to-indigo-800 text-white rounded-3xl p-6 sm:p-8 shadow-md">
        <span className="bg-white/20 text-white text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
          Field Technician Gateway
        </span>
        <h1 className="text-2xl sm:text-3xl font-extrabold mt-3">Field Portal — {user?.name}</h1>
        <p className="text-xs sm:text-sm text-blue-100 mt-1">
          {user?.department || 'Roads & Infrastructure Wing'} • {user?.ward || 'Ward 43 - MP Nagar'}
        </p>

        <div className="mt-5">
          <Button
            onClick={() => navigate('/worker/tasks')}
            className="bg-white text-blue-900 hover:bg-blue-50 font-bold"
            rightIcon={<ArrowRight className="w-4 h-4" />}
          >
            View Assigned Field Tasks ({pending + inProgress})
          </Button>
        </div>
      </div>

      {/* Worker Stats */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Assigned Queue" value={total} icon={<CheckSquare className="w-5 h-5 text-blue-600" />} />
        <StatCard title="In Progress" value={inProgress} icon={<Clock className="w-5 h-5 text-indigo-600" />} iconBgColor="bg-indigo-50" />
        <StatCard title="Completed" value={completed} icon={<CheckCircle2 className="w-5 h-5 text-emerald-600" />} iconBgColor="bg-emerald-50" />
        <StatCard title="Worker Points" value={user?.points || 820} icon={<Award className="w-5 h-5 text-amber-600" />} iconBgColor="bg-amber-50" />
      </div>

      {/* Today's Tasks Stream */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
        <div className="flex items-center justify-between">
          <h3 className="font-bold text-gray-900 text-base">Today's Priority Field Tasks</h3>
          <Button variant="ghost" size="sm" onClick={() => navigate('/worker/tasks')}>
            View All Tasks
          </Button>
        </div>

        <div className="space-y-3">
          {tasks.map((task) => (
            <div
              key={task.id}
              onClick={() => navigate(`/worker/tasks/${task.id}`)}
              className="p-4 rounded-2xl border border-gray-200 hover:border-blue-500 bg-gray-50/50 hover:bg-white transition-all cursor-pointer flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3"
            >
              <div className="space-y-1">
                <div className="flex items-center gap-2">
                  <span className="text-xs font-bold text-blue-800 bg-blue-50 px-2 py-0.5 rounded border border-blue-200">
                    {task.id}
                  </span>
                  <PriorityBadge priority={task.priority} />
                  <span className="text-[11px] font-semibold text-gray-500">{task.scheduledDate}</span>
                </div>
                <h4 className="font-bold text-gray-900 text-sm">{task.title}</h4>
                <p className="text-xs text-gray-500 flex items-center gap-1">
                  <MapPin className="w-3.5 h-3.5 text-blue-600" />
                  {task.location.address} ({task.location.ward})
                </p>
              </div>

              <Button size="sm" variant={task.status === 'IN_PROGRESS' ? 'primary' : 'outline'}>
                {task.status === 'IN_PROGRESS' ? 'Continue Task' : 'Open Details'}
              </Button>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}
