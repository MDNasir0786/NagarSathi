import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Sparkles, CheckCircle2, ArrowRight, ArrowLeft, AlertTriangle, MapPin, Camera } from 'lucide-react';
import { useAuthStore } from '../../stores/authStore';
import { complaintService, aiService } from '../../services';
import { FileUploader } from '../../components/ui/FileUploader';
import { AIInsightCard } from '../../components/ai/AIInsightCard';
import { Button } from '../../components/ui/Button';
import { COMPLAINT_CATEGORIES } from '../../types';

export default function RegisterComplaint() {
  const { user } = useAuthStore();
  const navigate = useNavigate();

  const [step, setStep] = useState(1);
  const [images, setImages] = useState([]);
  const [title, setTitle] = useState('');
  const [description, setDescription] = useState('');
  const [category, setCategory] = useState('Roads & Potholes');
  const [ward, setWard] = useState('Ward 48 - Arera Colony');
  const [address, setAddress] = useState('Link Road 1, Arera Colony, Bhopal');
  
  const [aiResult, setAiResult] = useState(null);
  const [analyzingAi, setAnalyzingAi] = useState(false);
  const [submitting, setSubmitting] = useState(false);
  const [submittedComplaint, setSubmittedComplaint] = useState(null);

  const handleNextStep1 = () => {
    if (images.length === 0) {
      alert('Please upload or select at least one photo evidence.');
      return;
    }
    setStep(2);
  };

  const handleAnalyzeAI = async () => {
    if (!description || description.length < 10) {
      alert('Please provide a detailed description (min 10 characters).');
      return;
    }
    setAnalyzingAi(true);
    try {
      const res = await aiService.analyzeImageAndDescription(description, category);
      setAiResult(res);
      setAnalyzingAi(false);
      setStep(3);
    } catch (e) {
      console.error(e);
      setAnalyzingAi(false);
      setStep(3);
    }
  };

  const handleFinalSubmit = async () => {
    setSubmitting(true);
    try {
      const newComplaint = await complaintService.createComplaint({
        title: title || `${category} reported at ${ward}`,
        description,
        category,
        priority: aiResult?.predictedPriority || 'MEDIUM',
        location: {
          address,
          ward,
          lat: 23.2315,
          lng: 77.4338,
        },
        citizenId: user?.id || 'cit-001',
        citizenName: user?.name || 'Rajesh Sharma',
        citizenPhone: user?.phone || '+91 98930 12345',
        images,
        aiAnalysis: aiResult || undefined,
      });

      setSubmittedComplaint(newComplaint);
      setSubmitting(false);
      setStep(4);
    } catch (e) {
      console.error(e);
      setSubmitting(false);
    }
  };

  return (
    <div className="max-w-3xl mx-auto space-y-6">
      {/* Header */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs">
        <h2 className="text-xl font-bold text-gray-900">Register Civic Complaint</h2>
        <p className="text-xs text-gray-500 mt-1">Multi-step geotagged issue registration with AI verification</p>

        {/* Progress Bar */}
        <div className="flex items-center justify-between mt-6 text-xs font-bold text-gray-500">
          <span className={step >= 1 ? 'text-emerald-700 font-extrabold' : ''}>1. Photo Evidence</span>
          <span className={step >= 2 ? 'text-emerald-700 font-extrabold' : ''}>2. Issue Details</span>
          <span className={step >= 3 ? 'text-emerald-700 font-extrabold' : ''}>3. AI Analysis</span>
          <span className={step >= 4 ? 'text-emerald-700 font-extrabold' : ''}>4. Confirmation</span>
        </div>
        <div className="w-full bg-gray-100 rounded-full h-2 mt-2">
          <div
            className="bg-emerald-600 h-2 rounded-full transition-all duration-300"
            style={{ width: `${(step / 4) * 100}%` }}
          />
        </div>
      </div>

      {/* Step 1: Upload Photo */}
      {step === 1 && (
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
          <h3 className="font-bold text-gray-900 text-sm flex items-center gap-2">
            <Camera className="w-4 h-4 text-emerald-600" />
            Step 1: Capture or Upload Issue Photo
          </h3>
          <FileUploader onImagesChange={(urls) => setImages(urls)} />
          <div className="flex justify-end pt-4">
            <Button onClick={handleNextStep1} rightIcon={<ArrowRight className="w-4 h-4" />}>
              Proceed to Issue Details
            </Button>
          </div>
        </div>
      )}

      {/* Step 2: Details */}
      {step === 2 && (
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
          <h3 className="font-bold text-gray-900 text-sm">Step 2: Enter Issue Description & Location</h3>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Complaint Title</label>
            <input
              type="text"
              placeholder="e.g. Deep Potholes on Link Road 1 near Board Office Square"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>

          <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Category</label>
              <select
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                {COMPLAINT_CATEGORIES.map((c) => (
                  <option key={c} value={c}>
                    {c}
                  </option>
                ))}
              </select>
            </div>

            <div>
              <label className="block text-xs font-semibold text-gray-700 mb-1">Bhopal Ward</label>
              <select
                value={ward}
                onChange={(e) => setWard(e.target.value)}
                className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
              >
                <option value="Ward 48 - Arera Colony">Ward 48 - Arera Colony</option>
                <option value="Ward 43 - MP Nagar Zone I">Ward 43 - MP Nagar Zone I</option>
                <option value="Ward 52 - Shahpura">Ward 52 - Shahpura</option>
                <option value="Ward 12 - Hamidia">Ward 12 - Hamidia</option>
                <option value="Ward 35 - New Market">Ward 35 - New Market</option>
              </select>
            </div>
          </div>

          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Detailed Description</label>
            <textarea
              rows={3}
              placeholder="Describe the issue, landmarks, hazard level and specific location details..."
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-emerald-500 focus:outline-none"
            />
          </div>

          <div className="flex items-center justify-between pt-4">
            <Button variant="outline" onClick={() => setStep(1)} leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Back
            </Button>
            <Button onClick={handleAnalyzeAI} isLoading={analyzingAi} rightIcon={<Sparkles className="w-4 h-4" />}>
              Analyze with Smart AI Engine
            </Button>
          </div>
        </div>
      )}

      {/* Step 3: AI Result Inspection */}
      {step === 3 && (
        <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
          <h3 className="font-bold text-gray-900 text-sm">Step 3: AI Analysis & Verification Inspection</h3>
          
          <AIInsightCard aiAnalysis={aiResult} />

          <div className="p-4 bg-gray-50 rounded-xl border border-gray-200 text-xs space-y-2">
            <h4 className="font-bold text-gray-900">Summary Before Final Submission:</h4>
            <p><span className="font-semibold text-gray-700">Title:</span> {title || category}</p>
            <p><span className="font-semibold text-gray-700">Location:</span> {address} ({ward})</p>
            <p><span className="font-semibold text-gray-700">Photos Attached:</span> {images.length} file(s)</p>
          </div>

          <div className="flex items-center justify-between pt-4">
            <Button variant="outline" onClick={() => setStep(2)} leftIcon={<ArrowLeft className="w-4 h-4" />}>
              Edit Details
            </Button>
            <Button onClick={handleFinalSubmit} isLoading={submitting} rightIcon={<CheckCircle2 className="w-4 h-4" />}>
              Confirm & Submit Complaint
            </Button>
          </div>
        </div>
      )}

      {/* Step 4: Final Success Screen */}
      {step === 4 && submittedComplaint && (
        <div className="bg-white border border-emerald-200 rounded-3xl p-8 shadow-lg text-center space-y-4">
          <div className="w-16 h-16 bg-emerald-100 text-emerald-600 rounded-full flex items-center justify-center mx-auto shadow-sm">
            <CheckCircle2 className="w-10 h-10" />
          </div>
          <h3 className="text-2xl font-extrabold text-gray-900">Complaint Registered Successfully!</h3>
          <p className="text-xs text-gray-600 max-w-md mx-auto">
            Your complaint has been assigned Tracking ID{' '}
            <span className="font-bold text-emerald-700 bg-emerald-50 px-2 py-0.5 rounded border border-emerald-200">
              {submittedComplaint.id}
            </span>
          </p>

          <div className="bg-emerald-50/60 p-4 rounded-2xl border border-emerald-100 max-w-md mx-auto text-xs text-emerald-900 text-left space-y-1">
            <p><span className="font-bold">Status:</span> {submittedComplaint.status}</p>
            <p><span className="font-bold">Ward:</span> {submittedComplaint.location.ward}</p>
            <p><span className="font-bold">Points Awarded:</span> +50 Smart Bhopal Citizen Points</p>
          </div>

          <div className="flex items-center justify-center gap-3 pt-4">
            <Button onClick={() => navigate('/citizen/complaints')} variant="primary">
              Track Complaint Status
            </Button>
            <Button onClick={() => navigate('/citizen/dashboard')} variant="outline">
              Return to Dashboard
            </Button>
          </div>
        </div>
      )}
    </div>
  );
}
