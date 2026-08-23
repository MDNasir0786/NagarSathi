import { z } from 'zod';

export const loginSchema = z.object({
  email: z.string().email('Please enter a valid email address'),
  password: z.string().min(6, 'Password must be at least 6 characters'),
  role: z.enum(['CITIZEN', 'WORKER', 'NODAL_OFFICER', 'NGO', 'HIGHER_AUTHORITY', 'SUPER_ADMIN']),
});

export const complaintRegistrationSchema = z.object({
  title: z.string().min(5, 'Title must be at least 5 characters'),
  description: z.string().min(15, 'Please provide a detailed description (min 15 characters)'),
  category: z.string().min(1, 'Please select a category'),
  ward: z.string().min(1, 'Please select a ward'),
  address: z.string().min(5, 'Location address is required'),
  images: z.array(z.string()).min(1, 'At least one geotagged photo evidence is required'),
});

export const workerTaskCompletionSchema = z.object({
  taskId: z.string(),
  notes: z.string().min(10, 'Please enter completion notes (min 10 characters)'),
  afterImages: z.array(z.string()).min(1, 'At least one resolution proof photo is required'),
});

export const volunteerSchema = z.object({
  name: z.string().min(3, 'Name is required'),
  email: z.string().email('Invalid email address'),
  phone: z.string().min(10, 'Phone number must be at least 10 digits'),
  ward: z.string().min(1, 'Select primary ward'),
});
