'use client';

import { MainLayout } from '@/components/layout/main-layout';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { useAuth } from '@/contexts/AuthContext';
import { useOwnerProfile } from '@/hooks/useApi';
import { Dog, Calendar, MapPin, Settings } from 'lucide-react';
import Link from 'next/link';

export default function DashboardPage(): JSX.Element {
  const { user } = useAuth();
  const { data: ownerProfile, isLoading, error } = useOwnerProfile();

  return (
    <MainLayout>
      <ProtectedRoute>
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
          {/* Welcome Header */}
          <div className="mb-8">
            <h1 className="text-3xl font-bold text-gray-900 mb-2">
              Welcome back, {user?.displayName?.split(' ')[0] || 'Dog Parent'}!
            </h1>
            <p className="text-gray-600">
              Manage your dogs, bookings, and find new care services
            </p>
          </div>

          {/* Account Status */}
          {isLoading && (
            <div className="mb-8">
              <Card>
                <CardContent className="flex items-center justify-center py-8">
                  <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
                  <span className="ml-3 text-gray-600">Loading your account...</span>
                </CardContent>
              </Card>
            </div>
          )}

          {error && (
            <div className="mb-8">
              <Card>
                <CardContent className="py-6">
                  <div className="text-center text-red-600">
                    <p className="font-medium">Unable to load account information</p>
                    <p className="text-sm mt-1">Please refresh the page or contact support if the problem persists.</p>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {ownerProfile && (
            <div className="mb-8">
              <Card className="bg-green-50 border-green-200">
                <CardContent className="py-6">
                  <div className="flex items-center">
                    <div className="bg-green-100 rounded-full p-2 mr-4">
                      <Dog className="h-6 w-6 text-green-600" />
                    </div>
                    <div>
                      <h3 className="font-semibold text-green-900">Account Active</h3>
                      <p className="text-sm text-green-700">
                        Your Dog Parking account is set up and ready to use!
                      </p>
                    </div>
                  </div>
                </CardContent>
              </Card>
            </div>
          )}

          {/* Quick Actions */}
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-8">
            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <Link href="/dogs">
                <CardHeader className="text-center">
                  <Dog className="h-12 w-12 text-blue-600 mx-auto mb-4" />
                  <CardTitle>My Dogs</CardTitle>
                  <CardDescription>
                    Add and manage your dog profiles
                  </CardDescription>
                </CardHeader>
              </Link>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <Link href="/venues">
                <CardHeader className="text-center">
                  <MapPin className="h-12 w-12 text-green-600 mx-auto mb-4" />
                  <CardTitle>Find Venues</CardTitle>
                  <CardDescription>
                    Discover dog care services near you
                  </CardDescription>
                </CardHeader>
              </Link>
            </Card>

            <Card className="hover:shadow-lg transition-shadow cursor-pointer">
              <Link href="/bookings">
                <CardHeader className="text-center">
                  <Calendar className="h-12 w-12 text-purple-600 mx-auto mb-4" />
                  <CardTitle>My Bookings</CardTitle>
                  <CardDescription>
                    View and manage your reservations
                  </CardDescription>
                </CardHeader>
              </Link>
            </Card>
          </div>

          {/* Getting Started Section */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center">
                <Settings className="h-5 w-5 mr-2" />
                Getting Started
              </CardTitle>
              <CardDescription>
                Complete these steps to make the most of Dog Parking
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-4">
                <div className="flex items-center p-4 bg-gray-50 rounded-lg">
                  <div className="bg-blue-100 rounded-full p-2 mr-4">
                    <Dog className="h-5 w-5 text-blue-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">Add your first dog</h4>
                    <p className="text-sm text-gray-600">Create a profile for your furry friend</p>
                  </div>
                  <Link href="/dogs">
                    <Button size="sm">Add Dog</Button>
                  </Link>
                </div>

                <div className="flex items-center p-4 bg-gray-50 rounded-lg">
                  <div className="bg-green-100 rounded-full p-2 mr-4">
                    <MapPin className="h-5 w-5 text-green-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">Explore venues</h4>
                    <p className="text-sm text-gray-600">Find the perfect care for your dog</p>
                  </div>
                  <Link href="/venues">
                    <Button size="sm" variant="outline">Browse</Button>
                  </Link>
                </div>

                <div className="flex items-center p-4 bg-gray-50 rounded-lg">
                  <div className="bg-purple-100 rounded-full p-2 mr-4">
                    <Calendar className="h-5 w-5 text-purple-600" />
                  </div>
                  <div className="flex-1">
                    <h4 className="font-medium text-gray-900">Make your first booking</h4>
                    <p className="text-sm text-gray-600">Schedule daycare, boarding, or grooming</p>
                  </div>
                  <Link href="/venues">
                    <Button size="sm" variant="outline">Book Now</Button>
                  </Link>
                </div>
              </div>
            </CardContent>
          </Card>
        </div>
      </ProtectedRoute>
    </MainLayout>
  );
}