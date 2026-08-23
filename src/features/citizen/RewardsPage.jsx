import React, { useEffect, useState } from 'react';
import { Award, ShieldCheck, Ticket, Crown, Download, CheckCircle2 } from 'lucide-react';
import { rewardService } from '../../services';
import { useAuthStore } from '../../stores/authStore';
import { StatCard } from '../../components/ui/StatCard';
import { Button } from '../../components/ui/Button';

export default function RewardsPage() {
  const { user } = useAuthStore();
  const [rewards, setRewards] = useState([]);
  const [downloadingCert, setDownloadingCert] = useState(false);

  useEffect(() => {
    rewardService.getRewards().then(setRewards);
  }, []);

  const handleDownloadCert = () => {
    setDownloadingCert(true);
    setTimeout(() => {
      setDownloadingCert(false);
      alert('Smart Bhopal Digital Certificate downloaded successfully!');
    }, 1000);
  };

  return (
    <div className="space-y-6">
      {/* Rewards Header */}
      <div className="bg-gradient-to-r from-emerald-700 to-teal-800 text-white rounded-3xl p-6 sm:p-8 shadow-md flex flex-col md:flex-row items-start md:items-center justify-between gap-4">
        <div>
          <span className="bg-white/20 text-white text-[11px] font-bold px-3 py-1 rounded-full uppercase tracking-wider">
            Smart Bhopal Gamification & Recognition
          </span>
          <h2 className="text-2xl sm:text-3xl font-extrabold mt-2">Rewards, Badges & Certificates</h2>
          <p className="text-xs sm:text-sm text-emerald-100 mt-1 max-w-xl">
            Earn points for every verified civic report. Unlock badges and official Bhopal Municipal Corporation certificates.
          </p>
        </div>

        <div className="bg-white/10 backdrop-blur-xs p-4 rounded-2xl border border-white/20 text-center min-w-36">
          <span className="text-xs text-emerald-100 font-semibold block uppercase">Total Balance</span>
          <span className="text-3xl font-black text-white">{user?.points || 450} PTS</span>
        </div>
      </div>

      {/* Stats Overview */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
        <StatCard title="Current Badge" value="Green Champion" icon={<ShieldCheck className="w-5 h-5 text-emerald-600" />} />
        <StatCard title="Ward Ranking" value="#4 in Ward 48" icon={<Crown className="w-5 h-5 text-amber-600" />} iconBgColor="bg-amber-50" />
        <StatCard title="Certificates" value="1 Unlocked" icon={<Award className="w-5 h-5 text-purple-600" />} iconBgColor="bg-purple-50" />
        <StatCard title="Vouchers" value="1 Available" icon={<Ticket className="w-5 h-5 text-blue-600" />} iconBgColor="bg-blue-50" />
      </div>

      {/* Badges Collection Grid */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs space-y-4">
        <h3 className="text-base font-bold text-gray-900">Your Badge & Achievement Collection</h3>

        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
          {rewards.map((item) => (
            <div
              key={item.id}
              className={`p-5 rounded-2xl border text-center space-y-2 transition-all ${
                item.unlocked
                  ? 'bg-emerald-50/50 border-emerald-200 shadow-xs'
                  : 'bg-gray-50 border-gray-200 opacity-60'
              }`}
            >
              <div className="w-12 h-12 bg-white rounded-2xl flex items-center justify-center mx-auto shadow-xs text-emerald-600 border border-emerald-100">
                <Award className="w-6 h-6" />
              </div>
              <h4 className="font-bold text-gray-900 text-xs">{item.title}</h4>
              <p className="text-[11px] text-gray-500 line-clamp-2 leading-relaxed">{item.description}</p>
              {item.unlocked ? (
                <span className="inline-flex items-center gap-1 text-[10px] font-bold text-emerald-700 bg-emerald-100 px-2 py-0.5 rounded-full">
                  <CheckCircle2 className="w-3 h-3" /> Unlocked
                </span>
              ) : (
                <span className="text-[10px] font-bold text-gray-500 bg-gray-200 px-2 py-0.5 rounded-full">
                  Requires {item.pointsRequired} PTS
                </span>
              )}
            </div>
          ))}
        </div>
      </div>

      {/* Digital Certificate Downloader */}
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex flex-col md:flex-row items-center justify-between gap-6">
        <div className="flex items-start gap-4">
          <div className="w-12 h-12 bg-purple-100 text-purple-700 rounded-2xl flex items-center justify-center shrink-0">
            <Award className="w-6 h-6" />
          </div>
          <div>
            <h3 className="font-bold text-gray-900 text-sm">Official Bhopal Civic Contributor Certificate</h3>
            <p className="text-xs text-gray-500 mt-0.5">
              Verified digital certificate issued by Bhopal Municipal Corporation for active civic governance participation.
            </p>
          </div>
        </div>

        <Button onClick={handleDownloadCert} isLoading={downloadingCert} leftIcon={<Download className="w-4 h-4" />}>
          Download Digital Certificate (PDF)
        </Button>
      </div>
    </div>
  );
}
