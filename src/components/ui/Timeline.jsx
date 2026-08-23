import React from 'react';
import { CheckCircle2, Clock, ShieldAlert, User, Wrench } from 'lucide-react';
import { format } from 'date-fns';

export const Timeline = ({ events = [] }) => {
  const getIcon = (role, status) => {
    if (status === 'Submitted') return <Clock className="w-4 h-4 text-blue-600" />;
    if (status === 'In Progress') return <Wrench className="w-4 h-4 text-indigo-600" />;
    if (status === 'Completed' || status === 'Verified') return <CheckCircle2 className="w-4 h-4 text-emerald-600" />;
    if (status === 'Escalated') return <ShieldAlert className="w-4 h-4 text-red-600" />;
    return <User className="w-4 h-4 text-gray-600" />;
  };

  const getBg = (status) => {
    if (status === 'Submitted') return 'bg-blue-100 ring-blue-300';
    if (status === 'In Progress') return 'bg-indigo-100 ring-indigo-300';
    if (status === 'Completed' || status === 'Verified') return 'bg-emerald-100 ring-emerald-300';
    if (status === 'Escalated') return 'bg-red-100 ring-red-300';
    return 'bg-gray-100 ring-gray-300';
  };

  return (
    <div className="flow-root">
      <ul role="list" className="-mb-8">
        {events.map((event, idx) => {
          const isLast = idx === events.length - 1;
          const formattedDate = (() => {
            try {
              return format(new Date(event.timestamp), 'MMM dd, yyyy • hh:mm a');
            } catch {
              return event.timestamp;
            }
          })();

          return (
            <li key={event.id || idx}>
              <div className="relative pb-8">
                {!isLast && (
                  <span
                    className="absolute top-4 left-4 -ml-px h-full w-0.5 bg-gray-200"
                    aria-hidden="true"
                  />
                )}
                <div className="relative flex items-start space-x-3">
                  <div>
                    <span className={`h-8 w-8 rounded-full flex items-center justify-center ring-4 ring-white ${getBg(event.status)}`}>
                      {getIcon(event.role, event.status)}
                    </span>
                  </div>
                  <div className="min-w-0 flex-1 bg-gray-50 border border-gray-100 rounded-lg p-3">
                    <div className="flex items-center justify-between">
                      <h4 className="text-sm font-semibold text-gray-900">{event.title}</h4>
                      <time className="text-xs text-gray-400">{formattedDate}</time>
                    </div>
                    <p className="mt-1 text-xs text-gray-600">{event.description}</p>
                    <div className="mt-2 flex items-center gap-2 text-xs text-gray-500">
                      <span className="font-medium text-emerald-800">{event.performedBy}</span>
                      <span>•</span>
                      <span className="bg-gray-200 text-gray-700 px-1.5 py-0.5 rounded text-[10px] uppercase font-bold">{event.role}</span>
                    </div>
                  </div>
                </div>
              </div>
            </li>
          );
        })}
      </ul>
    </div>
  );
};
