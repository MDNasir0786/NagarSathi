import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Lock,
  Mail,
  MapPin,
  Phone,
  ShieldCheck,
  User,
} from "lucide-react";

export const RegisterPage = () => {
  const navigate = useNavigate();

  // =====================================================
  // FORM STATE
  // =====================================================

  const [formData, setFormData] = useState({
    fullName: "",
    mobile: "",
    email: "",
    ward: "",
    password: "",
    confirmPassword: "",
  });

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  // =====================================================
  // HANDLE INPUT CHANGE
  // =====================================================

  const handleChange = (e) => {
    const { name, value } = e.target;

    setFormData((prev) => ({
      ...prev,
      [name]: value,
    }));

    // Remove previous error while user is typing
    if (error) {
      setError("");
    }
  };

  // =====================================================
  // HANDLE REGISTRATION
  // =====================================================

  const handleSubmit = async (e) => {
    e.preventDefault();

    setError("");

    // ---------------------------------------------------
    // FULL NAME VALIDATION
    // ---------------------------------------------------

    if (!formData.fullName.trim()) {
      setError("Please enter your full name.");
      return;
    }

    // ---------------------------------------------------
    // MOBILE VALIDATION
    // ---------------------------------------------------

    if (!/^[0-9]{10}$/.test(formData.mobile)) {
      setError("Please enter a valid 10-digit mobile number.");
      return;
    }

    // ---------------------------------------------------
    // EMAIL VALIDATION
    // ---------------------------------------------------

    if (!formData.email.trim()) {
      setError("Please enter your email address.");
      return;
    }

    // ---------------------------------------------------
    // WARD VALIDATION
    // ---------------------------------------------------

    if (!formData.ward) {
      setError("Please select your ward.");
      return;
    }

    // ---------------------------------------------------
    // PASSWORD VALIDATION
    // ---------------------------------------------------

    if (formData.password.length < 8) {
      setError("Password must be at least 8 characters.");
      return;
    }

    // ---------------------------------------------------
    // CONFIRM PASSWORD
    // ---------------------------------------------------

    if (formData.password !== formData.confirmPassword) {
      setError("Passwords do not match.");
      return;
    }

    try {
      setLoading(true);

      /*
       * ==================================================
       * SUPABASE AUTH WILL BE CONNECTED HERE
       * ==================================================
       *
       * Example:
       *
       * const { data, error } =
       *   await supabase.auth.signUp({
       *     email: formData.email,
       *     password: formData.password,
       *   });
       *
       * if (error) throw error;
       *
       * Then create the user's profile
       * inside your profiles table.
       *
       * ==================================================
       */

      console.log("Registration Data:", formData);

      // Temporary demo delay
      await new Promise((resolve) => setTimeout(resolve, 800));

      // After successful registration
      navigate("/login", {
        replace: true,
      });
    } catch (err) {
      console.error("Registration error:", err);

      setError("Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-[#f5fafb] text-slate-900">
      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="h-[68px] bg-white border-b border-slate-200 px-5 sm:px-8 lg:px-10 flex items-center justify-between">
        {/* ---------------------------------------------------
            LOGO
        --------------------------------------------------- */}

        <button
          type="button"
          onClick={() => navigate("/")}
          className="flex items-center gap-3"
        >
          <div className="text-[25px] font-black tracking-tight">
            <span className="text-[#0d2d56]">Smart</span>{" "}
            <span className="text-[#09945d]">Bhopal</span>
          </div>

          <span className="hidden sm:block text-xs text-slate-500 border-l border-slate-200 pl-3">
            Citizen Services
          </span>
        </button>

        {/* ---------------------------------------------------
            LOGIN BUTTON
        --------------------------------------------------- */}

        <button
          type="button"
          onClick={() => navigate("/login")}
          className="px-5 py-2 bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm hover:bg-emerald-800 transition"
        >
          Login
        </button>
      </header>

      {/* =====================================================
          MAIN CONTENT
      ===================================================== */}

      <main className="w-full max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
        {/* =================================================
            REGISTER CARD
        ================================================= */}

        <section className="grid grid-cols-1 lg:grid-cols-2 bg-white rounded-2xl overflow-hidden border border-slate-200 shadow-sm">
          {/* =================================================
              LEFT — BHOPAL IMAGE
          ================================================= */}

          <div
            className="relative min-h-[430px] sm:min-h-[500px] lg:min-h-[650px] bg-cover bg-center"
            style={{
              backgroundImage: "url('/bhopal.png')",
            }}
          >
            {/* ------------------------------------------------
                IMAGE OVERLAY
            ------------------------------------------------ */}

            <div className="absolute inset-0 bg-gradient-to-r from-[#062d58]/70 via-[#062d58]/35 to-[#062d58]/10" />

            {/* ------------------------------------------------
                HERO CONTENT
            ------------------------------------------------ */}

            <div className="relative z-10 h-full p-8 sm:p-12 lg:p-14 flex flex-col justify-start">
              <p className="text-sm font-bold tracking-wide text-emerald-200 mb-5 drop-shadow-sm">
                Join Smart Bhopal
              </p>

              <h1 className="text-4xl sm:text-5xl lg:text-[52px] font-black leading-[1.05] text-white max-w-lg drop-shadow-lg">
                Create your
                <br />
                Smart <span className="text-emerald-300">Bhopal</span>
                <br />
                account.
              </h1>

              {/* GREEN LINE */}

              <div className="w-12 h-1 bg-emerald-300 mt-6 mb-6 rounded-full" />

              {/* DESCRIPTION */}

              <p className="text-base sm:text-lg leading-7 text-white max-w-sm drop-shadow-md">
                Register once and access Smart Bhopal civic services from one
                secure account.
              </p>
            </div>
          </div>

          {/* =================================================
              RIGHT — REGISTER FORM
          ================================================= */}

          <div className="w-full p-6 sm:p-8 lg:p-10 xl:p-12 flex flex-col justify-center">
            {/* ------------------------------------------------
                FORM TITLE
            ------------------------------------------------ */}

            <div className="text-center mb-7">
              <h2 className="text-xl sm:text-2xl font-extrabold text-[#102b54]">
                Create Your Account
              </h2>

              <p className="text-xs sm:text-sm text-slate-500 mt-2">
                Register to access Smart Bhopal services
              </p>
            </div>

            {/* =================================================
                ERROR MESSAGE
            ================================================= */}

            {error && (
              <div className="mb-5 rounded-xl border border-red-200 bg-red-50 px-4 py-3 text-xs sm:text-sm text-red-600">
                {error}
              </div>
            )}

            {/* =================================================
                REGISTER FORM
            ================================================= */}

            <form onSubmit={handleSubmit} className="w-full space-y-4">
              {/* =================================================
                  FULL NAME
              ================================================= */}

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Full Name
                </label>

                <div className="relative w-full">
                  <User className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-600 pointer-events-none" />

                  <input
                    type="text"
                    name="fullName"
                    value={formData.fullName}
                    onChange={handleChange}
                    required
                    autoComplete="name"
                    placeholder="Enter your full name"
                    className="w-full pl-11 pr-4 py-3.5 text-sm border border-slate-200 rounded-xl outline-none bg-white focus:ring-2 focus:ring-emerald-200 focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* =================================================
                  MOBILE NUMBER
              ================================================= */}

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Mobile Number
                </label>

                <div className="w-full flex border border-slate-200 rounded-xl overflow-hidden bg-white focus-within:ring-2 focus-within:ring-emerald-200 focus-within:border-emerald-500">
                  <span className="flex items-center px-4 py-3.5 bg-slate-50 text-sm border-r border-slate-200 whitespace-nowrap">
                    🇮🇳 +91
                  </span>

                  <input
                    type="tel"
                    name="mobile"
                    value={formData.mobile}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, "");

                      setFormData((prev) => ({
                        ...prev,
                        mobile: value.slice(0, 10),
                      }));

                      if (error) {
                        setError("");
                      }
                    }}
                    required
                    maxLength={10}
                    pattern="[0-9]{10}"
                    autoComplete="tel"
                    placeholder="Enter mobile number"
                    className="w-full min-w-0 px-4 py-3.5 text-sm outline-none bg-transparent"
                  />

                  <Phone className="w-4 h-4 text-emerald-600 mr-4 self-center flex-shrink-0" />
                </div>
              </div>

              {/* =================================================
                  EMAIL
              ================================================= */}

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Email Address
                </label>

                <div className="relative w-full">
                  <Mail className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-600 pointer-events-none" />

                  <input
                    type="email"
                    name="email"
                    value={formData.email}
                    onChange={handleChange}
                    required
                    autoComplete="email"
                    placeholder="Enter email address"
                    className="w-full pl-11 pr-4 py-3.5 text-sm border border-slate-200 rounded-xl outline-none bg-white focus:ring-2 focus:ring-emerald-200 focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* =================================================
                  WARD
              ================================================= */}

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Ward
                </label>

                <div className="relative w-full">
                  <MapPin className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-600 pointer-events-none z-10" />

                  <select
                    name="ward"
                    value={formData.ward}
                    onChange={handleChange}
                    required
                    className="w-full pl-11 pr-4 py-3.5 text-sm border border-slate-200 rounded-xl outline-none focus:ring-2 focus:ring-emerald-200 focus:border-emerald-500 bg-white appearance-none cursor-pointer"
                  >
                    <option value="">Select your ward</option>

                    <option value="WARD_01">Ward 01</option>

                    <option value="WARD_02">Ward 02</option>

                    <option value="WARD_03">Ward 03</option>

                    <option value="WARD_04">Ward 04</option>

                    <option value="WARD_05">Ward 05</option>
                  </select>
                </div>
              </div>

              {/* =================================================
                  PASSWORD
              ================================================= */}

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Password
                </label>

                <div className="relative w-full">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-600 pointer-events-none" />

                  <input
                    type="password"
                    name="password"
                    value={formData.password}
                    onChange={handleChange}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    placeholder="Create password"
                    className="w-full pl-11 pr-4 py-3.5 text-sm border border-slate-200 rounded-xl outline-none bg-white focus:ring-2 focus:ring-emerald-200 focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* =================================================
                  CONFIRM PASSWORD
              ================================================= */}

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Confirm Password
                </label>

                <div className="relative w-full">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-600 pointer-events-none" />

                  <input
                    type="password"
                    name="confirmPassword"
                    value={formData.confirmPassword}
                    onChange={handleChange}
                    required
                    minLength={8}
                    autoComplete="new-password"
                    placeholder="Confirm password"
                    className="w-full pl-11 pr-4 py-3.5 text-sm border border-slate-200 rounded-xl outline-none bg-white focus:ring-2 focus:ring-emerald-200 focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* =================================================
                  TERMS
              ================================================= */}

              <label className="flex items-start gap-3 text-[11px] sm:text-xs text-slate-500 pt-1 cursor-pointer">
                <input
                  type="checkbox"
                  required
                  className="mt-0.5 w-4 h-4 accent-emerald-600 flex-shrink-0 cursor-pointer"
                />

                <span className="leading-5">
                  I agree to Smart Bhopal's{" "}
                  <button
                    type="button"
                    className="font-semibold text-emerald-700 hover:underline"
                  >
                    Terms & Conditions
                  </button>{" "}
                  and Privacy Policy.
                </span>
              </label>

              {/* =================================================
                  REGISTER BUTTON
              ================================================= */}

              <button
                type="submit"
                disabled={loading}
                className="w-full min-h-[50px] flex items-center justify-center gap-2 bg-emerald-700 hover:bg-emerald-800 disabled:bg-emerald-600 disabled:opacity-70 text-white py-3.5 rounded-xl text-sm font-semibold transition-all duration-200 shadow-sm"
              >
                {loading ? "Creating Account..." : "Create Account"}

                {!loading && <ArrowRight className="w-4 h-4" />}
              </button>
            </form>

            {/* =================================================
                LOGIN NAVIGATION
            ================================================= */}

            <div className="text-center mt-6 pt-5 border-t border-slate-100">
              <p className="text-sm text-slate-500">
                Already have an account?{" "}
                <button
                  type="button"
                  onClick={() => navigate("/login")}
                  className="font-bold text-emerald-700 hover:underline"
                >
                  Login
                </button>
              </p>
            </div>

            {/* =================================================
                SECURITY MESSAGE
            ================================================= */}

            <div className="flex items-center justify-center gap-2 mt-5 text-[10px] sm:text-xs text-slate-400">
              <ShieldCheck className="w-4 h-4 text-emerald-600 flex-shrink-0" />

              <span>Your information is protected and secure.</span>
            </div>
          </div>
        </section>
      </main>

      {/* =====================================================
          FOOTER
      ===================================================== */}

      <footer className="bg-[#062d58] text-white px-6 sm:px-10 py-8">
        <div className="max-w-[1280px] mx-auto grid sm:grid-cols-2 lg:grid-cols-4 gap-8 text-xs">
          {/* =================================================
              BRAND
          ================================================= */}

          <div>
            <div className="text-xl font-black">
              Smart <span className="text-emerald-400">Bhopal</span>
            </div>

            <p className="text-slate-300 mt-2">Citizen Services Portal</p>

            <p className="text-slate-400 mt-5 leading-5">
              © 2026 Smart Bhopal.
              <br />
              All rights reserved.
            </p>
          </div>

          {/* =================================================
              QUICK LINKS
          ================================================= */}

          <div>
            <h3 className="font-bold mb-3">Quick Links</h3>

            <div className="space-y-2 text-slate-300">
              <button
                type="button"
                onClick={() => navigate("/")}
                className="block hover:text-white transition"
              >
                Home
              </button>

              <button
                type="button"
                onClick={() => navigate("/about")}
                className="block hover:text-white transition"
              >
                About Us
              </button>

              <button
                type="button"
                onClick={() => navigate("/services")}
                className="block hover:text-white transition"
              >
                Services
              </button>

              <button
                type="button"
                onClick={() => navigate("/help")}
                className="block hover:text-white transition"
              >
                Help & Support
              </button>
            </div>
          </div>

          {/* =================================================
              CONTACT
          ================================================= */}

          <div>
            <h3 className="font-bold mb-3">Contact Us</h3>

            <p className="text-slate-300 leading-6">
              ☎ &nbsp;0755-xxxxxxx
              <br />
              ✉ &nbsp;help@smartbhopal.gov.in
              <br />⌖ &nbsp;Bhopal, Madhya Pradesh, India
            </p>
          </div>

          {/* =================================================
              SECURITY
          ================================================= */}

          <div>
            <div className="flex items-start gap-3">
              <ShieldCheck className="w-10 h-10 text-emerald-400 flex-shrink-0" />

              <div>
                <h3 className="font-bold">Your data is secure with us</h3>

                <p className="text-slate-300 mt-2 leading-5">
                  We respect your privacy and protect your information.
                </p>
              </div>
            </div>
          </div>
        </div>
      </footer>
    </div>
  );
};
