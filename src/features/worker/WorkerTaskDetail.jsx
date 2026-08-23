import React, { useEffect, useState } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { MapPin, Play, CheckCircle2, ArrowLeft, Camera, FileText, Wrench } from 'lucide-react';
import { taskService } from '../../services';
import { PriorityBadge } from '../../components/ui/PriorityBadge';
import { FileUploader } from '../../components/ui/FileUploader';
import { MapView } from '../../components/maps/MapView';
import { Button } from '../../components/ui/Button';

export default function WorkerTaskDetail() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [task, setTask] = useState(null);
  const [notes, setNotes] = useState('');
  const [proofImages, setProofImages] = useState([]);
  const [submitting, setSubmitting] = useState(false);
  const [success, setSuccess] = useState(false);

  useEffect(() => {
    taskService.getWorkerTasks().then((data) => {
      const found = data.find((t) => t.id === id) || data[0];
      if (found) {
        setTask(found);
        setNotes(found.workerNotes || '');
        setProofImages(found.afterImages || []);
      }
    });
  }, [id]);

  if (!task) return <div className="p-8 text-center text-xs text-gray-500">Loading Task Details...</div>;

  const handleStartTask = async () => {
    setSubmitting(true);
    const updated = await taskService.updateTaskState(task.id, 'IN_PROGRESS', 'Worker arrived on site and started work.');
    setTask(updated);
    setSubmitting(false);
  };

  const handleSubmitCompletion = async () => {
    if (proofImages.length === 0) {
      alert('Please upload at least one completion photo proof before submitting.');
      return;
    }
    setSubmitting(true);
    const updated = await taskService.updateTaskState(
      task.id,
      'COMPLETED_AWAITING_VERIFICATION',
      notes || 'Work completed on site. Asphalt patched and inspected.',
      proofImages
    );
    setTask(updated);
    setSubmitting(false);
    setSuccess(true);
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-3">
        <Button variant="outline" size="sm" onClick={() => navigate('/worker/tasks')} leftIcon={<ArrowLeft className="w-4 h-4" />}>
          Back to Task Queue
        </Button>

        <div className="flex items-start justify-between gap-3 pt-2">
          <div>
            <span className="text-xs font-bold text-blue-800 bg-blue-50 px-2.5 py-1 rounded border border-blue-200">
              Task ID: {task.id}
            </span>
            <h2 className="text-xl font-bold text-gray-900 mt-2">{task.title}</h2>
            <p className="text-xs text-gray-500 mt-0.5">{task.location.address} ({task.location.ward})</p>
          </div>
          <PriorityBadge priority={task.priority} />
        </div>

        <div className="bg-blue-50/60 p-4 rounded-xl border border-blue-100 text-xs text-blue-900 space-y-1">
          <p className="font-bold flex items-center gap-1.5">
            <Wrench className="w-4 h-4 text-blue-700" />
            Field Instructions:
          </p>
          <p>{task.instructions}</p>
        </div>
      </div>

      {/* Map Location */}
      <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
        <h3 className="text-xs font-bold text-gray-700 mb-2 flex items-center gap-1">
          <MapPin className="w-4 h-4 text-blue-600" />
          Location & Navigation Map
        </h3>
        <MapView
          center={[task.location.lat, task.location.lng]}
          zoom={14}
          height="220px"
          markers={[task]}
        />
      </div>

      {/* Before Images */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-3">
        <h3 className="text-xs font-bold text-gray-900">Before Work Images (Citizen Upload)</h3>
        <div className="grid grid-cols-2 gap-3">
          {task.beforeImages?.map((img, i) => (
            <img key={i} src={img} alt="Before work" className="w-full aspect-video object-cover rounded-xl border border-gray-200" />
          ))}
        </div>
      </div>

      {/* Execution Controls */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
        <h3 className="text-sm font-bold text-gray-900 border-b border-gray-100 pb-3">Field Execution Actions</h3>

        {task.status === 'PENDING' && (
          <div className="p-4 bg-amber-50 rounded-xl border border-amber-200 text-xs text-amber-900 flex items-center justify-between">
            <span>Task is currently PENDING. Click to mark start of work on site.</span>
            <Button onClick={handleStartTask} isLoading={submitting} leftIcon={<Play className="w-4 h-4" />}>
              Start Task
            </Button>
          </div>
        )}

        {(task.status === 'IN_PROGRESS' || task.status === 'COMPLETED_AWAITING_VERIFICATION') && (
          <div className="space-y-4">
            <FileUploader
              label="Upload Completion Proof Photos"
              helperText="Attach at least 1 clear photo of finished work on site."
              onImagesChange={(urls) => setProofImages(urls)}
            />

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Technician Notes</label>
              <textarea
                rows={3}
                placeholder="Enter work details, materials used, asphalt compaction notes..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-blue-500 focus:outline-none"
              />
            </div>

            <div className="pt-2 flex justify-end">
              <Button
                onClick={handleSubmitCompletion}
                isLoading={submitting}
                leftIcon={<CheckCircle2 className="w-4 h-4" />}
              >
                Submit Completion Proof
              </Button>
            </div>
          </div>
        )}

        {success && (
          <div className="p-4 bg-emerald-50 border border-emerald-200 rounded-xl text-emerald-900 text-xs font-bold text-center">
            Completion proof submitted successfully! Synced with Nodal Officer and Citizen timeline.
          </div>
        )}
      </div>
    </div>
  );
}
