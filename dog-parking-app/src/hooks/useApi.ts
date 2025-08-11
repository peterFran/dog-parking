'use client';

import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { apiClient } from '../lib/api-client';
import { useAuth } from '../contexts/AuthContext';

// Query Keys
export const QueryKeys = {
  venues: ['venues'],
  venue: (id: string) => ['venue', id],
  venueSlots: (id: string) => ['venue-slots', id],
  ownerProfile: ['owner-profile'],
  dogs: ['dogs'],
  dog: (id: string) => ['dog', id],
  bookings: ['bookings'],
  booking: (id: string) => ['booking', id],
} as const;

// Public API Hooks (no auth required)
export function useVenues() {
  return useQuery({
    queryKey: QueryKeys.venues,
    queryFn: () => apiClient.getVenues(),
  });
}

export function useVenue(id: string) {
  return useQuery({
    queryKey: QueryKeys.venue(id),
    queryFn: () => apiClient.getVenue(id),
    enabled: !!id,
  });
}

export function useVenueSlots(id: string) {
  return useQuery({
    queryKey: QueryKeys.venueSlots(id),
    queryFn: () => apiClient.getVenueSlots(id),
    enabled: !!id,
  });
}

// Protected API Hooks (auth required)
export function useOwnerProfile() {
  const { getIdToken, user } = useAuth();

  return useQuery({
    queryKey: QueryKeys.ownerProfile,
    queryFn: async () => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.getOwnerProfile(token);
    },
    enabled: !!user,
  });
}

export function useRegisterOwner() {
  const { getIdToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: any) => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.registerOwner(data, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.ownerProfile });
    },
  });
}

export function useUpdateOwnerProfile() {
  const { getIdToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: any) => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.updateOwnerProfile(data, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.ownerProfile });
    },
  });
}

export function useDogs() {
  const { getIdToken, user } = useAuth();

  return useQuery({
    queryKey: QueryKeys.dogs,
    queryFn: async () => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.getDogs(token);
    },
    enabled: !!user,
  });
}

export function useDog(id: string) {
  const { getIdToken, user } = useAuth();

  return useQuery({
    queryKey: QueryKeys.dog(id),
    queryFn: async () => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.getDog(id, token);
    },
    enabled: !!user && !!id,
  });
}

export function useCreateDog() {
  const { getIdToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: any) => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.createDog(data, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.dogs });
    },
  });
}

export function useUpdateDog() {
  const { getIdToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.updateDog(id, data, token);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.dogs });
      queryClient.invalidateQueries({ queryKey: QueryKeys.dog(id) });
    },
  });
}

export function useDeleteDog() {
  const { getIdToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.deleteDog(id, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.dogs });
    },
  });
}

export function useBookings() {
  const { getIdToken, user } = useAuth();

  return useQuery({
    queryKey: QueryKeys.bookings,
    queryFn: async () => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.getBookings(token);
    },
    enabled: !!user,
  });
}

export function useBooking(id: string) {
  const { getIdToken, user } = useAuth();

  return useQuery({
    queryKey: QueryKeys.booking(id),
    queryFn: async () => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.getBooking(id, token);
    },
    enabled: !!user && !!id,
  });
}

export function useCreateBooking() {
  const { getIdToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (data: any) => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.createBooking(data, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.bookings });
    },
  });
}

export function useUpdateBooking() {
  const { getIdToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async ({ id, data }: { id: string; data: any }) => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.updateBooking(id, data, token);
    },
    onSuccess: (_, { id }) => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.bookings });
      queryClient.invalidateQueries({ queryKey: QueryKeys.booking(id) });
    },
  });
}

export function useCancelBooking() {
  const { getIdToken } = useAuth();
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn: async (id: string) => {
      const token = await getIdToken();
      if (!token) throw new Error('No auth token');
      return apiClient.cancelBooking(id, token);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: QueryKeys.bookings });
    },
  });
}