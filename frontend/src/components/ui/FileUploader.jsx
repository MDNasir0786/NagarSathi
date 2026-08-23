import React, { useRef, useState } from 'react';
import { UploadCloud, Image as ImageIcon, X, AlertCircle } from 'lucide-react';
import { Button } from './Button';

export const FileUploader = ({
  onImagesChange,
  maxFiles = 3,
  label = 'Upload Photo Evidence',
  helperText = 'Supported formats: JPG, PNG, WEBP up to 5MB. Geotagged images recommended.',
}) => {
  const [previews, setPreviews] = useState([]);
  const [error, setError] = useState(null);
  const fileInputRef = useRef(null);

  const handleFiles = (files) => {
    if (!files) return;
    setError(null);

    const validFiles = [];
    for (let i = 0; i < files.length; i++) {
      const file = files[i];
      if (!['image/jpeg', 'image/png', 'image/webp'].includes(file.type)) {
        setError('Invalid file type. Only JPG, PNG, WEBP are allowed.');
        return;
      }
      if (file.size > 5 * 1024 * 1024) {
        setError('File size exceeds 5MB limit.');
        return;
      }
      validFiles.push(file);
    }

    const newPreviews = validFiles.map((file) => URL.createObjectURL(file));
    const combined = [...previews, ...newPreviews].slice(0, maxFiles);
    setPreviews(combined);
    if (onImagesChange) onImagesChange(combined);
  };

  const removeImage = (index) => {
    const updated = previews.filter((_, i) => i !== index);
    setPreviews(updated);
    if (onImagesChange) onImagesChange(updated);
  };

  const addSamplePreset = (url) => {
    if (previews.length >= maxFiles) return;
    const updated = [...previews, url];
    setPreviews(updated);
    if (onImagesChange) onImagesChange(updated);
  };

  return (
    <div className="space-y-3">
      {label && <label className="block text-sm font-semibold text-gray-800">{label}</label>}

      {/* Drag & Drop Zone */}
      <div
        onClick={() => fileInputRef.current?.click()}
        className="border-2 border-dashed border-emerald-300 hover:border-emerald-500 bg-emerald-50/30 hover:bg-emerald-50/70 rounded-xl p-6 text-center cursor-pointer transition-all duration-200"
      >
        <input
          ref={fileInputRef}
          type="file"
          accept="image/jpeg,image/png,image/webp"
          multiple={maxFiles > 1}
          className="hidden"
          onChange={(e) => handleFiles(e.target.files)}
        />
        <div className="mx-auto w-12 h-12 bg-emerald-100 text-emerald-700 rounded-full flex items-center justify-center mb-3">
          <UploadCloud className="w-6 h-6" />
        </div>
        <p className="text-sm font-medium text-gray-800">
          <span className="text-emerald-700 font-semibold">Click to upload</span> or drag and drop photo
        </p>
        <p className="text-xs text-gray-500 mt-1">{helperText}</p>
      </div>

      {error && (
        <div className="flex items-center gap-2 text-xs text-red-600 bg-red-50 p-2.5 rounded-lg border border-red-100">
          <AlertCircle className="w-4 h-4 shrink-0" />
          <span>{error}</span>
        </div>
      )}

      {/* Preset Quick Select for easy demo testing */}
      <div className="flex items-center gap-2 pt-1">
        <span className="text-xs text-gray-500 font-medium">Quick Sample Photos:</span>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => addSamplePreset('https://images.unsplash.com/photo-1515162816999-a0c47dc192f7?w=600&auto=format&fit=crop&q=80')}
          leftIcon={<ImageIcon className="w-3.5 h-3.5 text-emerald-600" />}
        >
          Sample Pothole
        </Button>
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() => addSamplePreset('https://images.unsplash.com/photo-1541888946425-d0fbb186a5b3?w=600&auto=format&fit=crop&q=80')}
          leftIcon={<ImageIcon className="w-3.5 h-3.5 text-blue-600" />}
        >
          Sample Leakage
        </Button>
      </div>

      {/* Image Previews */}
      {previews.length > 0 && (
        <div className="grid grid-cols-3 gap-3 pt-2">
          {previews.map((src, i) => (
            <div key={i} className="relative group rounded-lg overflow-hidden border border-gray-200 aspect-video bg-gray-100">
              <img src={src} alt={`Upload preview ${i + 1}`} className="w-full h-full object-cover" />
              <button
                type="button"
                onClick={(e) => {
                  e.stopPropagation();
                  removeImage(i);
                }}
                className="absolute top-1 right-1 p-1 bg-red-600 text-white rounded-full opacity-90 hover:opacity-100 shadow-md transition-opacity"
              >
                <X className="w-3.5 h-3.5" />
              </button>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};
