// Domain constants & enums for Smart Bhopal JavaScript Frontend

export const USER_ROLES = {
  CITIZEN: 'CITIZEN',
  WORKER: 'WORKER',
  NODAL_OFFICER: 'NODAL_OFFICER',
  NGO: 'NGO',
  HIGHER_AUTHORITY: 'HIGHER_AUTHORITY',
  SUPER_ADMIN: 'SUPER_ADMIN',
};

export const COMPLAINT_CATEGORIES = [
  'Roads & Potholes',
  'Water Supply & Sewage',
  'Garbage & Sanitation',
  'Street Lighting',
  'Parks & Public Amenities',
  'Encroachment & Construction',
  'Stray Animals',
  'Traffic & Transport',
];

export const PRIORITY_LEVELS = {
  CRITICAL: 'CRITICAL',
  HIGH: 'HIGH',
  MEDIUM: 'MEDIUM',
  LOW: 'LOW',
};

export const COMPLAINT_STATUSES = {
  SUBMITTED: 'Submitted',
  IN_REVIEW: 'In Review',
  ASSIGNED: 'Assigned',
  IN_PROGRESS: 'In Progress',
  COMPLETED: 'Completed',
  VERIFIED: 'Verified',
  CLOSED: 'Closed',
  ESCALATED: 'Escalated',
};
