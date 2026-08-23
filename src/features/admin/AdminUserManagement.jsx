import React, { useState } from 'react';
import { UserPlus, Search, Shield, Edit, Trash2 } from 'lucide-react';
import { MOCK_USERS } from '../../services/mockData';
import { DataTable } from '../../components/ui/DataTable';
import { Button } from '../../components/ui/Button';
import { Modal } from '../../components/ui/Modal';

export default function AdminUserManagement() {
  const [users, setUsers] = useState(Object.values(MOCK_USERS));
  const [search, setSearch] = useState('');
  const [editUser, setEditUser] = useState(null);

  const filtered = users.filter(
    (u) =>
      u.name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()) ||
      u.role.toLowerCase().includes(search.toLowerCase())
  );

  const handleRoleChange = (userId, newRole) => {
    setUsers(users.map((u) => (u.id === userId ? { ...u, role: newRole } : u)));
    setEditUser(null);
    alert('User role updated successfully.');
  };

  const columns = [
    {
      header: 'Name',
      cell: (row) => (
        <div className="flex items-center gap-2">
          <img src={row.avatar} alt={row.name} className="w-7 h-7 rounded-full object-cover border" />
          <span className="font-bold text-gray-900">{row.name}</span>
        </div>
      ),
    },
    {
      header: 'Email',
      accessorKey: 'email',
    },
    {
      header: 'Role',
      cell: (row) => (
        <span className="font-bold text-xs bg-slate-100 text-slate-800 px-2 py-0.5 rounded border border-slate-200">
          {row.role}
        </span>
      ),
    },
    {
      header: 'Department / Ward',
      cell: (row) => row.ward || row.department || 'All Wards',
    },
    {
      header: 'Action',
      cell: (row) => (
        <Button size="sm" variant="outline" onClick={() => setEditUser(row)} leftIcon={<Edit className="w-3.5 h-3.5" />}>
          Edit Role
        </Button>
      ),
    },
  ];

  return (
    <div className="space-y-6">
      <div className="bg-white border border-gray-200 rounded-2xl p-6 shadow-xs flex flex-col sm:flex-row items-start sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-gray-900">User & Access Management</h2>
          <p className="text-xs text-gray-500">Manage user accounts, assign roles & configure administrative permissions</p>
        </div>

        <Button leftIcon={<UserPlus className="w-4 h-4" />}>Add New User Account</Button>
      </div>

      <div className="bg-white border border-gray-200 rounded-2xl p-4 shadow-xs">
        <div className="relative max-w-md">
          <Search className="w-4 h-4 text-gray-400 absolute left-3 top-2.5" />
          <input
            type="text"
            placeholder="Search users by name, email, or role..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="w-full pl-9 pr-4 py-2 text-xs border border-gray-300 rounded-xl focus:ring-2 focus:ring-slate-800 focus:outline-none"
          />
        </div>
      </div>

      <DataTable columns={columns} data={filtered} keyExtractor={(r) => r.id} />

      {/* Edit Role Modal */}
      {editUser && (
        <Modal isOpen={!!editUser} onClose={() => setEditUser(null)} title={`Edit Role for ${editUser.name}`}>
          <div className="space-y-4">
            <p className="text-xs text-gray-600">Select new role for {editUser.email}:</p>
            <div className="space-y-2">
              {['CITIZEN', 'WORKER', 'NODAL_OFFICER', 'NGO', 'HIGHER_AUTHORITY', 'SUPER_ADMIN'].map((r) => (
                <button
                  key={r}
                  onClick={() => handleRoleChange(editUser.id, r)}
                  className={`w-full text-left px-4 py-2.5 rounded-xl border text-xs font-bold transition-all ${
                    editUser.role === r ? 'bg-slate-900 text-white border-slate-900' : 'bg-gray-50 text-gray-800 border-gray-200 hover:bg-slate-100'
                  }`}
                >
                  {r}
                </button>
              ))}
            </div>
          </div>
        </Modal>
      )}
    </div>
  );
}
