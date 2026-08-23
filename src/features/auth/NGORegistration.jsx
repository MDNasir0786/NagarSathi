import React, { useState } from "react";
import {
  ArrowLeft,
  Building2,
  CheckCircle2,
  Mail,
  Phone,
  UserRound,
} from "lucide-react";
import { useNavigate } from "react-router-dom";
import { Button } from "../../components/ui/Button";

export const NGORegistration = () => {
  const navigate = useNavigate();
  const [submitted, setSubmitted] = useState(false);
  const [form, setForm] = useState({
    organization: "",
    contactName: "",
    email: "",
    phone: "",
  });

  const updateField = (event) => {
    setForm((current) => ({
      ...current,
      [event.target.name]: event.target.value,
    }));
  };

  const handleSubmit = (event) => {
    event.preventDefault();
    localStorage.setItem(
      "smart_bhopal_ngo_registration",
      JSON.stringify({ ...form, submittedAt: new Date().toISOString() }),
    );
    setSubmitted(true);
  };

  if (submitted) {
    return (
      <div className="min-h-screen bg-[#f5fafb] flex items-center justify-center p-5">
        <div className="bg-white border border-emerald-100 rounded-2xl shadow-lg max-w-md w-full p-8 text-center">
          <CheckCircle2 className="w-14 h-14 text-emerald-600 mx-auto mb-4" />
          <h1 className="text-2xl font-black text-[#102b54]">
            Registration Request Sent
          </h1>
          <p className="text-sm text-slate-500 mt-2">
            Our team will review your NGO details and contact you shortly.
          </p>
          <Button
            onClick={() => navigate("/login")}
            className="mt-6 w-full !bg-emerald-700 !rounded-lg"
            rightIcon={<ArrowLeft className="w-4 h-4" />}
          >
            Back to Login
          </Button>
        </div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-[#f5fafb] text-slate-900 flex items-center justify-center p-5">
      <div className="bg-white border border-slate-200 rounded-2xl shadow-lg max-w-lg w-full p-6 sm:p-9">
        <button
          type="button"
          onClick={() => navigate("/login")}
          className="flex items-center gap-2 text-xs font-semibold text-emerald-700 hover:text-emerald-900"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Login
        </button>
        <div className="mt-7 mb-6">
          <div className="w-12 h-12 rounded-xl bg-emerald-100 text-emerald-700 flex items-center justify-center mb-4">
            <Building2 className="w-6 h-6" />
          </div>
          <h1 className="text-2xl font-black text-[#102b54]">
            Register your NGO
          </h1>
          <p className="text-sm text-slate-500 mt-1">
            Join Smart Bhopal and collaborate on civic initiatives.
          </p>
        </div>
        <form onSubmit={handleSubmit} className="space-y-4">
          <label className="block text-xs font-bold text-slate-700">
            Organization Name
            <div className="relative mt-1.5">
              <Building2 className="absolute left-3 top-2.5 w-4 h-4 text-emerald-600" />
              <input
                name="organization"
                value={form.organization}
                onChange={updateField}
                required
                placeholder="Enter NGO name"
                className="w-full pl-9 pr-3 py-2.5 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-emerald-200"
              />
            </div>
          </label>
          <label className="block text-xs font-bold text-slate-700">
            Contact Person
            <div className="relative mt-1.5">
              <UserRound className="absolute left-3 top-2.5 w-4 h-4 text-emerald-600" />
              <input
                name="contactName"
                value={form.contactName}
                onChange={updateField}
                required
                placeholder="Full name"
                className="w-full pl-9 pr-3 py-2.5 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-emerald-200"
              />
            </div>
          </label>
          <div className="grid sm:grid-cols-2 gap-4">
            <label className="block text-xs font-bold text-slate-700">
              Email
              <div className="relative mt-1.5">
                <Mail className="absolute left-3 top-2.5 w-4 h-4 text-emerald-600" />
                <input
                  type="email"
                  name="email"
                  value={form.email}
                  onChange={updateField}
                  required
                  placeholder="ngo@example.com"
                  className="w-full pl-9 pr-3 py-2.5 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-emerald-200"
                />
              </div>
            </label>
            <label className="block text-xs font-bold text-slate-700">
              Mobile Number
              <div className="relative mt-1.5">
                <Phone className="absolute left-3 top-2.5 w-4 h-4 text-emerald-600" />
                <input
                  type="tel"
                  name="phone"
                  value={form.phone}
                  onChange={updateField}
                  required
                  placeholder="+91 mobile number"
                  className="w-full pl-9 pr-3 py-2.5 text-sm border border-slate-200 rounded-lg outline-none focus:ring-2 focus:ring-emerald-200"
                />
              </div>
            </label>
          </div>
          <Button
            type="submit"
            className="w-full !bg-emerald-700 hover:!bg-emerald-800 !rounded-lg !py-3 mt-2"
          >
            Submit Registration Request
          </Button>
        </form>
      </div>
    </div>
  );
};
