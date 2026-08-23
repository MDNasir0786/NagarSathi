import { 
  MOCK_USERS, 
  INITIAL_COMPLAINTS, 
  INITIAL_WORKER_TASKS, 
  INITIAL_NGO_AREAS, 
  INITIAL_VOLUNTEERS, 
  INITIAL_EVENTS, 
  INITIAL_REWARDS, 
  INITIAL_NOTIFICATIONS, 
  ANALYTICS_DATA, 
  INITIAL_AUDIT_LOGS 
} from './mockData';
import { apiClient, USE_MOCK } from './apiClient';
import { isSupabaseConfigured, supabase } from './supabaseClient';

// Helper for LocalStorage Persistence in JavaScript
const getStoredData = (key, initial) => {
  try {
    const item = localStorage.getItem(`smart_bhopal_${key}`);
    return item ? JSON.parse(item) : initial;
  } catch (e) {
    console.warn(`LocalStorage read error for ${key}:`, e);
    return initial;
  }
};

const setStoredData = (key, value) => {
  try {
    localStorage.setItem(`smart_bhopal_${key}`, JSON.stringify(value));
  } catch (e) {
    console.warn(`LocalStorage write error for ${key}:`, e);
  }
};

// 1. Auth Service
export const authService = {
  async signInWithOAuth(provider) {
    if (!isSupabaseConfigured || !supabase) {
      throw new Error('Supabase is not configured. Add the VITE_SUPABASE variables.');
    }
    const { error } = await supabase.auth.signInWithOAuth({
      provider,
      options: { redirectTo: window.location.origin + '/login' },
    });
    if (error) throw error;
  },

  async signOut() {
    if (supabase) await supabase.auth.signOut();
  },

  async getCurrentUser(role) {
    if (!USE_MOCK) {
      const response = await apiClient.get('/auth/me');
      return mapProfile(response.profile);
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
    return MOCK_USERS[role] || MOCK_USERS.CITIZEN;
  },

  async login(email, role) {
    if (!USE_MOCK) {
      const response = await apiClient.get('/auth/me');
      return mapProfile(response.profile);
    }
    await new Promise((resolve) => setTimeout(resolve, 300));
    const user = MOCK_USERS[role] || {
      id: `usr-${Date.now()}`,
      name: email.split('@')[0],
      email,
      phone: '+91 98000 00000',
      role,
    };
    return user;
  },
};

// 2. Complaint Service
export const complaintService = {
  async getComplaints(filter = {}) {
    if (!USE_MOCK) {
      const response = await apiClient.get('/complaints', {
        ...(filter.search ? { search: filter.search } : {}),
      });
      return response.items.map(mapComplaint);
    }
    await new Promise((resolve) => setTimeout(resolve, 200));
    let complaints = getStoredData('complaints', INITIAL_COMPLAINTS);
    
    if (filter.search) {
      const q = filter.search.toLowerCase();
      complaints = complaints.filter(
        (c) => c.title.toLowerCase().includes(q) || c.id.toLowerCase().includes(q) || c.location.ward.toLowerCase().includes(q)
      );
    }
    if (filter.status && filter.status !== 'ALL') {
      complaints = complaints.filter((c) => c.status === filter.status);
    }
    if (filter.priority && filter.priority !== 'ALL') {
      complaints = complaints.filter((c) => c.priority === filter.priority);
    }
    if (filter.ward && filter.ward !== 'ALL') {
      complaints = complaints.filter((c) => c.location.ward.includes(filter.ward));
    }
    return complaints;
  },

  async getComplaintById(id) {
    if (!USE_MOCK) {
      return mapComplaint(await apiClient.get(`/complaints/${id}`));
    }
    await new Promise((resolve) => setTimeout(resolve, 150));
    const complaints = getStoredData('complaints', INITIAL_COMPLAINTS);
    return complaints.find((c) => c.id === id) || null;
  },

  async createComplaint(payload) {
    if (!USE_MOCK) {
      const response = await apiClient.post('/complaints', {
        title: payload.title,
        description: payload.description,
        latitude: payload.location?.lat,
        longitude: payload.location?.lng,
        address: payload.location?.address,
        ward: payload.location?.ward,
        image_url: payload.images?.[0] || null,
        image_urls: payload.images || [],
        category_hint: payload.category,
      });
      return mapComplaint(response.complaint);
    }
    await new Promise((resolve) => setTimeout(resolve, 400));
    const complaints = getStoredData('complaints', INITIAL_COMPLAINTS);
    const newId = `SB-2026-${Math.floor(8900 + Math.random() * 900)}`;
    const now = new Date().toISOString();

    const newComplaint = {
      ...payload,
      id: newId,
      status: 'Submitted',
      createdAt: now,
      updatedAt: now,
      timeline: [
        {
          id: `tl-${Date.now()}`,
          status: 'Submitted',
          title: 'Complaint Registered',
          description: 'Geotagged complaint logged with Smart Bhopal AI assistant.',
          timestamp: now,
          performedBy: payload.citizenName,
          role: 'CITIZEN',
        },
      ],
    };

    const updatedList = [newComplaint, ...complaints];
    setStoredData('complaints', updatedList);
    return newComplaint;
  },

  async updateComplaintStatus(id, status, actor, notes = '', extraFields = {}) {
    if (!USE_MOCK) {
      return mapComplaint(await apiClient.patch(`/complaints/${id}`, {
        description: notes || undefined,
      }));
    }
    await new Promise((resolve) => setTimeout(resolve, 250));
    const complaints = getStoredData('complaints', INITIAL_COMPLAINTS);
    const index = complaints.findIndex((c) => c.id === id);
    if (index === -1) throw new Error('Complaint not found');

    const target = complaints[index];
    const now = new Date().toISOString();
    const newTimelineEvent = {
      id: `tl-${Date.now()}`,
      status,
      title: `Status set to ${status}`,
      description: notes || `Complaint updated by ${actor.name}`,
      timestamp: now,
      performedBy: actor.name,
      role: actor.role,
    };

    const updated = {
      ...target,
      ...extraFields,
      status,
      updatedAt: now,
      timeline: [newTimelineEvent, ...target.timeline],
    };

    complaints[index] = updated;
    setStoredData('complaints', complaints);
    return updated;
  },
};

function mapProfile(profile) {
  return {
    ...profile,
    name: profile.full_name || profile.email,
    role: String(profile.role || 'citizen').toUpperCase(),
  };
}

function mapComplaint(complaint) {
  return {
    ...complaint,
    referenceCode: complaint.reference_code,
    id: complaint.id,
    createdAt: complaint.created_at,
    updatedAt: complaint.updated_at,
    priority: complaint.priority_score >= 80 ? 'CRITICAL' : complaint.priority_score >= 50 ? 'HIGH' : 'MEDIUM',
    location: {
      address: complaint.address || 'Bhopal',
      ward: complaint.ward || 'Unassigned',
      lat: complaint.latitude,
      lng: complaint.longitude,
    },
    images: complaint.image_urls || (complaint.image_url ? [complaint.image_url] : []),
    timeline: complaint.timeline || [],
  };
}

// 3. Worker & Task Service
export const taskService = {
  async getWorkerTasks() {
    await new Promise((resolve) => setTimeout(resolve, 200));
    return getStoredData('worker_tasks', INITIAL_WORKER_TASKS);
  },

  async updateTaskState(taskId, status, notes = '', afterImages = []) {
    await new Promise((resolve) => setTimeout(resolve, 300));
    const tasks = getStoredData('worker_tasks', INITIAL_WORKER_TASKS);
    const index = tasks.findIndex((t) => t.id === taskId);
    if (index === -1) throw new Error('Task not found');

    const target = tasks[index];
    const updated = {
      ...target,
      status,
      workerNotes: notes || target.workerNotes,
      afterImages: afterImages.length > 0 ? afterImages : target.afterImages,
      completedAt: status === 'COMPLETED_AWAITING_VERIFICATION' || status === 'VERIFIED' ? new Date().toISOString() : target.completedAt,
    };

    tasks[index] = updated;
    setStoredData('worker_tasks', tasks);

    // Also update parent complaint timeline if exists
    if (target.complaintId) {
      const complaintStatus = status === 'IN_PROGRESS' ? 'In Progress' : status === 'COMPLETED_AWAITING_VERIFICATION' ? 'Completed' : 'Verified';
      complaintService.updateComplaintStatus(
        target.complaintId,
        complaintStatus,
        { name: 'Vikram Singh', role: 'WORKER' },
        notes ? `Worker update: ${notes}` : `Worker set status to ${status}`,
        status === 'COMPLETED_AWAITING_VERIFICATION' ? {
          resolutionProof: {
            images: afterImages || [],
            notes: notes || 'Work completed by field technician.',
            completedAt: new Date().toISOString(),
          }
        } : {}
      ).catch(() => {});
    }

    return updated;
  },
};

// 4. NGO Service
export const ngoService = {
  async getNGOAreas() {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getStoredData('ngo_areas', INITIAL_NGO_AREAS);
  },

  async getVolunteers() {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getStoredData('volunteers', INITIAL_VOLUNTEERS);
  },

  async addVolunteer(volunteer) {
    await new Promise((resolve) => setTimeout(resolve, 250));
    const list = getStoredData('volunteers', INITIAL_VOLUNTEERS);
    const newVol = {
      ...volunteer,
      id: `vol-${Date.now()}`,
      joinedDate: new Date().toISOString().split('T')[0],
      assignedActivitiesCount: 0,
      pointsEarned: 50,
    };
    const updated = [newVol, ...list];
    setStoredData('volunteers', updated);
    return newVol;
  },

  async getCommunityEvents() {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getStoredData('events', INITIAL_EVENTS);
  },
};

// 5. Analytics Service
export const analyticsService = {
  async getSummary() {
    await new Promise((resolve) => setTimeout(resolve, 200));
    const complaints = getStoredData('complaints', INITIAL_COMPLAINTS);
    const total = complaints.length;
    const resolved = complaints.filter((c) => c.status === 'Completed' || c.status === 'Verified' || c.status === 'Closed').length;
    const active = complaints.filter((c) => c.status === 'In Progress' || c.status === 'Assigned' || c.status === 'In Review').length;
    const escalated = complaints.filter((c) => c.isEscalated || c.status === 'Escalated').length;

    return {
      ...ANALYTICS_DATA,
      totalComplaints: total,
      resolvedComplaints: resolved,
      activeComplaints: active,
      escalatedComplaints: escalated,
    };
  },
};

// 6. AI Service
export const aiService = {
  async analyzeImageAndDescription(description, categorySelected) {
    await new Promise((resolve) => setTimeout(resolve, 800));
    const descLower = description.toLowerCase();
    
    let autoCategory = 'Roads & Potholes';
    let priority = 'MEDIUM';
    let dept = 'Road Maintenance Wing';

    if (descLower.includes('water') || descLower.includes('pipe') || descLower.includes('leak') || descLower.includes('drain')) {
      autoCategory = 'Water Supply & Sewage';
      priority = descLower.includes('burst') || descLower.includes('flood') ? 'CRITICAL' : 'HIGH';
      dept = 'Jal Nigam & Municipal Hydraulics';
    } else if (descLower.includes('garbage') || descLower.includes('waste') || descLower.includes('trash') || descLower.includes('dump')) {
      autoCategory = 'Garbage & Sanitation';
      priority = 'MEDIUM';
      dept = 'Solid Waste Management';
    } else if (descLower.includes('light') || descLower.includes('dark') || descLower.includes('lamp') || descLower.includes('pole')) {
      autoCategory = 'Street Lighting';
      priority = 'MEDIUM';
      dept = 'Electrical & Lighting Cell';
    } else if (descLower.includes('pothole') || descLower.includes('road') || descLower.includes('tar') || descLower.includes('crater')) {
      autoCategory = 'Roads & Potholes';
      priority = descLower.includes('deep') || descLower.includes('accident') ? 'HIGH' : 'MEDIUM';
      dept = 'Road Maintenance Wing';
    }

    const isDuplicate = descLower.includes('board office') || descLower.includes('link road');

    return {
      autoCategory: categorySelected || autoCategory,
      predictedPriority: priority,
      confidenceScore: 0.93,
      isDuplicateDetected: isDuplicate,
      duplicateComplaintId: isDuplicate ? 'SB-2026-8901' : undefined,
      duplicateSimilarity: isDuplicate ? 0.89 : undefined,
      recommendedWorkerDept: dept,
      imageVerified: true,
      imageVerificationNote: 'AI model successfully recognized civic damage pattern in uploaded photo.',
    };
  },
};

// 7. Notification Service
export const notificationService = {
  async getNotifications() {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getStoredData('notifications', INITIAL_NOTIFICATIONS);
  },

  async markAsRead(id) {
    const list = getStoredData('notifications', INITIAL_NOTIFICATIONS);
    const updated = list.map((n) => (n.id === id ? { ...n, read: true } : n));
    setStoredData('notifications', updated);
  },
};

// 8. Reward Service
export const rewardService = {
  async getRewards() {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getStoredData('rewards', INITIAL_REWARDS);
  },
};

// 9. Admin Service
export const adminService = {
  async getAuditLogs() {
    await new Promise((resolve) => setTimeout(resolve, 150));
    return getStoredData('audit_logs', INITIAL_AUDIT_LOGS);
  },
};
