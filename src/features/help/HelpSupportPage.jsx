import React from 'react';
import { HelpCircle, PhoneCall, Mail, MessageSquare } from 'lucide-react';
import { Button } from '../../components/ui/Button';

export default function HelpSupportPage() {
  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-sm">
        <div className="flex items-center gap-3 mb-4">
          <div className="p-3 bg-emerald-50 text-emerald-600 rounded-xl">
            <HelpCircle className="w-6 h-6" />
          </div>
          <div>
            <h2 className="text-lg font-bold text-gray-900">Smart Bhopal Help & Support Center</h2>
            <p className="text-xs text-gray-500">Citizen Helpline, Municipal FAQs, & Support Tickets</p>
          </div>
        </div>

        <div className="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
          <div className="border border-gray-200 rounded-xl p-4 bg-gray-50/50">
            <PhoneCall className="w-5 h-5 text-emerald-600 mb-2" />
            <h3 className="text-sm font-bold text-gray-900">24x7 BMC Helpline</h3>
            <p className="text-xs text-gray-500 mt-1">Toll Free: 1800-233-0014</p>
          </div>
          <div className="border border-gray-200 rounded-xl p-4 bg-gray-50/50">
            <Mail className="w-5 h-5 text-emerald-600 mb-2" />
            <h3 className="text-sm font-bold text-gray-900">Email Support</h3>
            <p className="text-xs text-gray-500 mt-1">support@smartbhopal.gov.in</p>
          </div>
          <div className="border border-gray-200 rounded-xl p-4 bg-gray-50/50">
            <MessageSquare className="w-5 h-5 text-emerald-600 mb-2" />
            <h3 className="text-sm font-bold text-gray-900">WhatsApp Assistant</h3>
            <p className="text-xs text-gray-500 mt-1">+91 75525 00000</p>
          </div>
        </div>
      </div>
    </div>
  );
}
