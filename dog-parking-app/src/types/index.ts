export interface Owner {
  user_id: string;
  preferences: {
    notifications: boolean;
    marketing_emails: boolean;
    preferred_communication: 'email' | 'sms' | 'phone';
  };
  created_at: string;
  updated_at: string;
}

export interface Dog {
  id: string;
  owner_id: string;
  name: string;
  breed: string;
  age: number;
  size: 'small' | 'medium' | 'large' | 'extra-large';
  vaccination_status: 'up-to-date' | 'overdue' | 'unknown';
  special_needs: string[];
  emergency_contact: string;
  created_at: string;
  updated_at: string;
}

export interface Venue {
  id: string;
  name: string;
  address: string;
  city: string;
  state: string;
  zip_code: string;
  phone: string;
  email: string;
  description: string;
  amenities: string[];
  pricing: {
    hourly_rate: number;
    daily_rate: number;
    monthly_rate: number;
  };
  capacity: {
    small_dogs: number;
    medium_dogs: number;
    large_dogs: number;
    extra_large_dogs: number;
  };
  hours: {
    [key: string]: {
      open: string;
      close: string;
    };
  };
  created_at: string;
  updated_at: string;
}

export interface Booking {
  id: string;
  owner_id: string;
  dog_id: string;
  venue_id: string;
  service_type: 'daycare' | 'boarding' | 'grooming' | 'training';
  start_time: string;
  end_time: string;
  status: 'pending' | 'confirmed' | 'in-progress' | 'completed' | 'cancelled';
  special_instructions?: string;
  total_cost: number;
  created_at: string;
  updated_at: string;
  dog?: Dog;
  venue?: Venue;
}

export interface VenueSlot {
  id: string;
  venue_id: string;
  date: string;
  start_time: string;
  end_time: string;
  capacity: number;
  available_spots: number;
  price: number;
  service_type: 'daycare' | 'boarding' | 'grooming' | 'training';
}

export interface CreateDogRequest {
  name: string;
  breed: string;
  age: number;
  size: 'small' | 'medium' | 'large' | 'extra-large';
  vaccination_status: 'up-to-date' | 'overdue' | 'unknown';
  special_needs: string[];
  emergency_contact: string;
}

export interface CreateBookingRequest {
  dog_id: string;
  venue_id: string;
  service_type: 'daycare' | 'boarding' | 'grooming' | 'training';
  start_time: string;
  end_time: string;
  special_instructions?: string;
}

export interface OwnerPreferences {
  notifications: boolean;
  marketing_emails: boolean;
  preferred_communication: 'email' | 'sms' | 'phone';
}