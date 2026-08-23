import React, { useRef, useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  ArrowRight,
  Building2,
  Clock3,
  HardHat,
  Lock,
  ShieldCheck,
  Sparkles,
  UsersRound,
} from "lucide-react";

import { useAuthStore } from "../../stores/authStore";
import { Button } from "../../components/ui/Button";
import { USER_ROLES } from "../../types";

export const LoginPage = () => {
  const { login } = useAuthStore();
  const navigate = useNavigate();

  const [mobile, setMobile] = useState("");
  const [password, setPassword] = useState("");
  const [selectedRole, setSelectedRole] = useState("CITIZEN");
  const [loading, setLoading] = useState(false);

  const formRef = useRef(null);

  // =====================================================
  // ROLE CONFIGURATION
  // =====================================================

  const roleMeta = {
    CITIZEN: {
      label: "Citizen",
      detail: "Access services and track requests.",
      icon: UsersRound,
    },

    WORKER: {
      label: "Worker",
      detail: "Manage and update field tasks.",
      icon: HardHat,
    },

    NODAL_OFFICER: {
      label: "Nodal Officer",
      detail: "Review and approve tasks.",
      icon: Building2,
    },

    SUPER_ADMIN: {
      label: "Admin",
      detail: "Manage system and users.",
      icon: ShieldCheck,
    },

    NGO: {
      label: "NGO",
      detail: "Collaborate and manage initiatives.",
      icon: Sparkles,
    },

    HIGHER_AUTHORITY: {
      label: "Authority",
      detail: "Monitor city-wide performance.",
      icon: ShieldCheck,
    },
  };

  // =====================================================
  // ROLE ROUTES
  // =====================================================

  const rolePaths = {
    CITIZEN: "/citizen/dashboard",
    WORKER: "/worker/dashboard",
    NODAL_OFFICER: "/nodal/dashboard",
    NGO: "/ngo/dashboard",
    HIGHER_AUTHORITY: "/authority/dashboard",
    SUPER_ADMIN: "/admin/dashboard",
  };

  // =====================================================
  // FOCUS LOGIN
  // =====================================================

  const focusLoginForm = () => {
    formRef.current?.scrollIntoView({
      behavior: "smooth",
      block: "center",
    });

    formRef.current?.querySelector("input")?.focus({
      preventScroll: true,
    });
  };

  // =====================================================
  // LOGIN
  // =====================================================

  const handleSubmit = async (e) => {
    e.preventDefault();

    try {
      setLoading(true);

      await login(mobile, selectedRole);

      navigate(rolePaths[selectedRole] || "/citizen/dashboard", {
        replace: true,
      });
    } catch (error) {
      console.error("Login failed:", error);
    } finally {
      setLoading(false);
    }
  };

  // =====================================================
  // AVAILABLE ROLES
  // =====================================================

  const availableRoles = Object.keys(USER_ROLES).filter(
    (role) => role !== "HIGHER_AUTHORITY",
  );

  return (
    <div className="min-h-screen bg-[#f5fafb] text-slate-900">
      {/* =====================================================
          HEADER
      ===================================================== */}

      <header className="h-[68px] bg-white border-b border-slate-200 px-5 sm:px-8 lg:px-10 flex items-center justify-between">
        {/* LOGO */}

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

        {/* HEADER ACTIONS */}

        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={() => navigate("/ngo/register")}
            className="hidden sm:block px-4 py-2 border border-emerald-600 text-emerald-700 rounded-lg text-xs font-semibold hover:bg-emerald-50 transition"
          >
            Register NGO
          </button>

          <button
            type="button"
            onClick={focusLoginForm}
            className="px-5 py-2 bg-emerald-700 text-white rounded-lg text-xs font-semibold shadow-sm hover:bg-emerald-800 transition"
          >
            Login
          </button>
        </div>
      </header>

      {/* =====================================================
          MAIN
      ===================================================== */}

      <main className="w-full max-w-[1280px] mx-auto px-4 sm:px-6 lg:px-8 py-6 lg:py-8">
        {/* =================================================
            MAIN LOGIN CARD
        ================================================= */}

        <section className="grid grid-cols-1 lg:grid-cols-[1fr_1fr] bg-white rounded-2xl overflow-hidden border border-slate-200 shadow-sm">
          {/* =================================================
              LEFT IMAGE
          ================================================= */}

          <div
            className="relative min-h-[420px] sm:min-h-[500px] lg:min-h-[650px] bg-cover bg-center"
            style={{
              backgroundImage: "url('/bhopal.png')",
            }}
          >
            {/* IMAGE OVERLAY */}

            <div className="absolute inset-0 bg-gradient-to-r from-[#062d58]/70 via-[#062d58]/35 to-[#062d58]/10" />

            {/* IMAGE CONTENT */}

            <div className="relative z-10 h-full p-8 sm:p-12 lg:p-14 flex flex-col justify-start">
              <p className="text-sm font-bold tracking-wide text-emerald-200 mb-5 drop-shadow-sm">
                A smarter city starts with you
              </p>

              <h1 className="text-4xl sm:text-5xl lg:text-[52px] font-black leading-[1.05] text-white max-w-lg drop-shadow-lg">
                Welcome to
                <br />
                Smart <span className="text-emerald-300">Bhopal</span>
              </h1>

              <div className="w-12 h-1 bg-emerald-300 mt-6 mb-6 rounded-full" />

              <p className="text-base sm:text-lg leading-7 text-white max-w-sm drop-shadow-md">
                Login to continue making
                <br />
                Bhopal better{" "}
                <span className="font-bold text-emerald-300">together.</span>
              </p>
            </div>
          </div>

          {/* =================================================
              RIGHT LOGIN PANEL
          ================================================= */}

          <div className="w-full p-6 sm:p-8 lg:p-10 xl:p-12 flex flex-col justify-center">
            {/* =================================================
                TITLE
            ================================================= */}

            <div className="text-center mb-7">
              <h2 className="text-xl sm:text-2xl font-extrabold text-[#102b54]">
                Login to Your Account
              </h2>

              <p className="text-xs sm:text-sm text-slate-500 mt-2">
                Please select who you are to continue
              </p>
            </div>

            {/* =================================================
                ROLE CARDS
            ================================================= */}

            <div className="grid grid-cols-2 sm:grid-cols-3 lg:grid-cols-3 xl:grid-cols-5 gap-2.5 mb-6">
              {availableRoles.map((role) => {
                const meta = roleMeta[role];

                if (!meta) {
                  return null;
                }

                const Icon = meta.icon;

                const isSelected = selectedRole === role;

                return (
                  <button
                    key={role}
                    type="button"
                    onClick={() => setSelectedRole(role)}
                    className={`
                      min-h-[100px]
                      w-full
                      px-2
                      py-3
                      rounded-xl
                      border
                      flex
                      flex-col
                      items-center
                      justify-center
                      text-center
                      transition-all
                      duration-200
                      ${
                        isSelected
                          ? "border-emerald-600 bg-emerald-50 shadow-sm"
                          : "border-slate-200 bg-white hover:border-emerald-300 hover:bg-slate-50"
                      }
                    `}
                  >
                    <Icon
                      className={`
                        w-7 h-7 mb-2
                        ${isSelected ? "text-emerald-700" : "text-blue-700"}
                      `}
                    />

                    <span className="text-[11px] font-bold text-slate-800">
                      {meta.label}
                    </span>

                    <span className="hidden xl:block text-[8px] leading-3 text-slate-500 mt-1">
                      {meta.detail}
                    </span>
                  </button>
                );
              })}
            </div>

            {/* =================================================
                OR
            ================================================= */}

            <div className="flex items-center gap-3 text-[10px] text-slate-400 mb-5">
              <span className="h-px bg-slate-200 flex-1" />

              <span>OR</span>

              <span className="h-px bg-slate-200 flex-1" />
            </div>

            {/* =================================================
                FORM
            ================================================= */}

            <form
              ref={formRef}
              onSubmit={handleSubmit}
              className="w-full space-y-4"
            >
              {/* MOBILE */}

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
                    value={mobile}
                    onChange={(e) => {
                      const value = e.target.value.replace(/\D/g, "");

                      setMobile(value.slice(0, 10));
                    }}
                    required
                    maxLength={10}
                    pattern="[0-9]{10}"
                    placeholder="Enter mobile number"
                    className="w-full min-w-0 px-4 py-3.5 text-sm outline-none bg-transparent"
                  />
                </div>
              </div>

              {/* PASSWORD */}

              <div>
                <label className="block text-xs font-bold text-slate-700 mb-2">
                  Password
                </label>

                <div className="relative w-full">
                  <Lock className="absolute left-4 top-1/2 -translate-y-1/2 w-4 h-4 text-emerald-600 pointer-events-none" />

                  <input
                    type="password"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    required
                    placeholder="Enter password"
                    className="w-full pl-11 pr-4 py-3.5 text-sm border border-slate-200 rounded-xl outline-none bg-white focus:ring-2 focus:ring-emerald-200 focus:border-emerald-500"
                  />
                </div>
              </div>

              {/* FORGOT */}

              <div className="flex justify-end">
                <button
                  type="button"
                  onClick={() => navigate("/forgot-password")}
                  className="text-xs text-emerald-700 font-semibold hover:underline"
                >
                  Forgot Password?
                </button>
              </div>

              {/* LOGIN */}

              <Button
                type="submit"
                isLoading={loading}
                className="w-full !bg-emerald-700 hover:!bg-emerald-800 !rounded-xl !py-3.5 !text-sm"
                rightIcon={<ArrowRight className="w-4 h-4" />}
              >
                Login
              </Button>
            </form>

            {/* =================================================
                REGISTER
            ================================================= */}

            <div className="text-center mt-6">
              <p className="text-sm text-slate-500">
                Don't have an account?{" "}
                <button
                  type="button"
                  onClick={() => navigate("/register")}
                  className="font-bold text-emerald-700 hover:underline"
                >
                  Register
                </button>
              </p>
            </div>

            {/* =================================================
                SOCIAL DIVIDER
            ================================================= */}

            <div className="flex items-center gap-3 text-[10px] text-slate-400 my-5">
              <span className="h-px bg-slate-200 flex-1" />
              OR
              <span className="text-slate-400">OR</span>
              <span className="h-px bg-slate-200 flex-1" />
            </div>

            {/* =================================================
                SOCIAL LOGIN
            ================================================= */}

            <p className="text-center text-xs text-slate-500 mb-3">
              Login with
            </p>

            <div className="grid grid-cols-3 gap-2.5">
              <button
                type="button"
                className="h-11 border border-slate-200 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
              >
                <span className="text-red-500 font-bold">G</span>
                &nbsp; Google
              </button>

              <button
                type="button"
                className="h-11 border border-slate-200 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
              >
                <span className="text-blue-600 font-bold">f</span>
                &nbsp; Facebook
              </button>

              <button
                type="button"
                className="h-11 border border-slate-200 rounded-xl text-xs font-semibold hover:bg-slate-50 transition"
              >
                <span className="font-bold">Apple</span>
              </button>
            </div>
          </div>
        </section>

        {/* =================================================
            FEATURE STRIP
        ================================================= */}

        <section className="grid sm:grid-cols-3 bg-white border-x border-b border-slate-200 rounded-b-2xl divide-y sm:divide-y-0 sm:divide-x divide-slate-200">
          {/* SECURE */}

          <div className="flex items-center justify-center gap-3 px-5 py-5">
            <ShieldCheck className="w-8 h-8 text-emerald-600 flex-shrink-0" />

            <div>
              <h3 className="text-xs font-bold text-[#12335b]">
                Secure & Safe
              </h3>

              <p className="text-[10px] text-slate-500 mt-1">
                Your data is protected with top security.
              </p>
            </div>
          </div>

          {/* EASY */}

          <div className="flex items-center justify-center gap-3 px-5 py-5">
            <Clock3 className="w-8 h-8 text-blue-600 flex-shrink-0" />

            <div>
              <h3 className="text-xs font-bold text-[#12335b]">Easy Access</h3>

              <p className="text-[10px] text-slate-500 mt-1">
                Access services anytime, anywhere.
              </p>
            </div>
          </div>

          {/* TOGETHER */}

          <div className="flex items-center justify-center gap-3 px-5 py-5">
            <UsersRound className="w-8 h-8 text-purple-600 flex-shrink-0" />

            <div>
              <h3 className="text-xs font-bold text-[#12335b]">
                Better Together
              </h3>

              <p className="text-[10px] text-slate-500 mt-1">
                Building a better Bhopal with everyone.
              </p>
            </div>
          </div>
        </section>
      </main>

      {/* =====================================================
          FOOTER
      ===================================================== */}

      <footer className="bg-[#062d58] text-white px-6 sm:px-10 py-8">
        <div className="max-w-[1280px] mx-auto grid sm:grid-cols-2 lg:grid-cols-4 gap-8 text-xs">
          {/* BRAND */}

          <div>
            <div className="text-xl font-black">
              Smart <span className="text-emerald-400">Bhopal</span>
            </div>

            <p className="text-slate-300 mt-2">Citizen Services Portal</p>

            <p className="text-slate-400 mt-5">
              © 2026 Smart Bhopal.
              <br />
              All rights reserved.
            </p>
          </div>

          {/* QUICK LINKS */}

          <div>
            <h3 className="font-bold mb-3">Quick Links</h3>

            <div className="space-y-2 text-slate-300">
              <button
                type="button"
                onClick={() => navigate("/")}
                className="block hover:text-white"
              >
                Home
              </button>

              <button
                type="button"
                onClick={() => navigate("/about")}
                className="block hover:text-white"
              >
                About Us
              </button>

              <button
                type="button"
                onClick={() => navigate("/services")}
                className="block hover:text-white"
              >
                Services
              </button>

              <button
                type="button"
                onClick={() => navigate("/help")}
                className="block hover:text-white"
              >
                Help & Support
              </button>
            </div>
          </div>

          {/* CONTACT */}

          <div>
            <h3 className="font-bold mb-3">Contact Us</h3>

            <p className="text-slate-300 leading-6">
              ☎ &nbsp;0755-xxxxxxx
              <br />
              ✉ &nbsp;help@smartbhopal.gov.in
              <br />⌖ &nbsp;Bhopal, Madhya Pradesh, India
            </p>
          </div>

          {/* SECURITY */}

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
