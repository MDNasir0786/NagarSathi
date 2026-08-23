import React, { useEffect, useState } from 'react';
import { UserPlus, Search, Users, Mail, Phone, MapPin } from 'lucide-react';
import { ngoService } from '../../services';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';
import { DataTable } from '../../components/ui/DataTable';

export default function NGOVolunteers() {
  const [volunteers, setVolunteers] = useState([]);
  const [search, setSearch] = useState('');
  const [modalOpen, setModalOpen] = useState(false);

  const [name, setName] = useState('');
  const [email, setEmail] = useState('');
  const [phone, setPhone] = useState('');
  const [ward, setWard] = useState('Ward 48 - Arera Colony');
  const [submitting, setSubmitting] = useState(false);

  useEffect(() => {
    ngoService.getVolunteers().then(setVolunteers);
  }, []);

  const handleAddVolunteer = async (e) => {
    e.preventDefault();
    setSubmitting(true);
    const newVol = await ngoService.addVolunteer({ name, email, phone, ward, status: 'ACTIVE' });
    setVolunteers([newVol, ...volunteers]);
    setSubmitting(false);
    setModalOpen(false);
    setName('');
    setEmail('');
    setPhone('');
  };

  const filtered = volunteers.filter(
    (v) =>
      v.name.toLowerCase().includes(search.toLowerCase()) ||
      v.email.toLowerCase().includes(search.toLowerCase()) ||
      v.ward.toLowerCase().includes(search.toLowerCase())
  );

  const columns = [
    {
      header: 'Volunteer Name',
      cell: (row) => <span className="font-bold text-gray-900">{row.name}</span>,
    },
    {
      header: 'Email',
      accessorKey: 'email',
    },
    {
      header: 'Phone',
      accessorKey: 'phone',
    },
    {
      header: 'Ward',
      cell: (row) => row.ward,
    },
    {
      header: 'Status',
      cell: (row) => (
        <span className={`text-[10px] font-bold px-2 py-0.5 rounded-full ${row.status === 'ACTIVE' ? 'bg-emerald-100 text-emerald-800' : 'bg-gray-100 text-gray-600'}`}>
          {row.status}
        </span>
      ),
    },
    {
      header: 'Points',
      accessorKey: 'pointsEarned',
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">Volunteer Roster & Management</h2>
          <p className="text-xs text-gray-500">Track active community volunteers and drive participations</p>
        </div>

        <Button onClick={() => setModalOpen(true)} leftIcon={<UserPlus className="w-4 h-4" />}>
          Register New Volunteer
        </Button>
      </div>

      {/* Search */}
      <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
        <div className="relative max-w-md">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search volunteer name, email, ward..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:outline-none"
          />
        </div>
      </div>

      <DataTable columns={columns} data={filtered} keyExtractor={(row) => row.id} />

      {/* Add Volunteer Modal */}
      <Modal isOpen={modalOpen} onClose={() => setModalOpen(false)} title="Register Community Volunteer">
        <form onSubmit={handleAddVolunteer} className="space-y-4">
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Full Name</label>
            <input
              type="text"
              required
              placeholder="e.g. Anish Gupta"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Email Address</label>
            <input
              type="email"
              required
              placeholder="anish.g@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Phone Number</label>
            <input
              type="text"
              required
              placeholder="+91 98270 00000"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:outline-none"
            />
          </div>
          <div>
            <label className="block text-xs font-semibold text-gray-700 mb-1">Primary Ward</label>
            <select
              value={ward}
              onChange={(e) => setWard(e.target.value)}
              className="w-full px-3 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-teal-500 focus:outline-none"
            >
              <option value="Ward 48 - Arera Colony">Ward 48 - Arera Colony</option>
              <option value="Ward 52 - Shahpura">Ward 52 - Shahpura</option>
              <option value="Ward 43 - MP Nagar">Ward 43 - MP Nagar</option>
            </select>
          </div>
          <div className="pt-2 flex justify-end">
            <Button type="submit" isLoading={submitting}>
              Add Volunteer
            </Button>
          </div>
        </form>
      </Modal>
    </div>
  );
}
