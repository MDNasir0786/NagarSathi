// Smart Bhopal Foundation Architectural Tests
import { describe, it, expect } from 'vitest';
import { USER_ROLES, COMPLAINT_CATEGORIES } from '../types/index.js';

describe('Smart Bhopal Foundation Architecture', () => {
  it('defines all 6 user roles in JS domain model', () => {
    expect(USER_ROLES.CITIZEN).toBe('CITIZEN');
    expect(USER_ROLES.WORKER).toBe('WORKER');
    expect(USER_ROLES.NODAL_OFFICER).toBe('NODAL_OFFICER');
    expect(USER_ROLES.NGO).toBe('NGO');
    expect(USER_ROLES.HIGHER_AUTHORITY).toBe('HIGHER_AUTHORITY');
    expect(USER_ROLES.SUPER_ADMIN).toBe('SUPER_ADMIN');
  });

  it('includes core civic complaint categories', () => {
    expect(COMPLAINT_CATEGORIES).toContain('Roads & Potholes');
    expect(COMPLAINT_CATEGORIES).toContain('Water Supply & Sewage');
    expect(COMPLAINT_CATEGORIES).toContain('Garbage & Sanitation');
  });
});
