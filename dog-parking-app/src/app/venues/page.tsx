'use client';

import { MainLayout } from '../../components/layout/main-layout';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '../../components/ui/card';
import { Button } from '../../components/ui/button';
import { useVenues } from '../../hooks/useApi';
import { MapPin, Phone, Mail, Star, Clock } from 'lucide-react';
import Link from 'next/link';
import { Venue } from '../../types';

export default function VenuesPage() {
  const { data: venuesData, isLoading, error } = useVenues();

  if (isLoading) {
    return (
      <MainLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="animate-spin rounded-full h-32 w-32 border-b-2 border-blue-600"></div>
        </div>
      </MainLayout>
    );
  }

  if (error) {
    return (
      <MainLayout>
        <div className="min-h-screen flex items-center justify-center">
          <div className="text-center">
            <h2 className="text-2xl font-bold text-gray-900 mb-4">
              Unable to load venues
            </h2>
            <p className="text-gray-600 mb-4">
              We're having trouble connecting to our services. Please try again later.
            </p>
            <Button onClick={() => window.location.reload()}>
              Try Again
            </Button>
          </div>
        </div>
      </MainLayout>
    );
  }

  const venues = (venuesData as any)?.venues || [];

  return (
    <MainLayout>
      <div className="bg-gray-50 py-8">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="text-center mb-8">
            <h1 className="text-3xl md:text-4xl font-bold text-gray-900 mb-4">
              Find Dog Care Venues
            </h1>
            <p className="text-xl text-gray-600">
              Discover trusted dog care providers in your area
            </p>
          </div>

          {venues.length === 0 ? (
            <div className="text-center py-12">
              <h3 className="text-xl font-semibold text-gray-900 mb-4">
                No venues available yet
              </h3>
              <p className="text-gray-600 mb-6">
                We're working on adding venues to our platform. Check back soon!
              </p>
              <Link href="/">
                <Button>Back to Home</Button>
              </Link>
            </div>
          ) : (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {venues.map((venue: Venue) => (
                <Card key={venue.id} className="hover:shadow-lg transition-shadow">
                  <CardHeader>
                    <CardTitle className="flex items-start justify-between">
                      <span>{venue.name}</span>
                      <div className="flex items-center text-yellow-500">
                        <Star className="h-4 w-4 fill-current" />
                        <span className="text-sm text-gray-600 ml-1">4.8</span>
                      </div>
                    </CardTitle>
                    <CardDescription className="flex items-center text-gray-600">
                      <MapPin className="h-4 w-4 mr-1" />
                      {venue.address}, {venue.city}, {venue.state} {venue.zip_code}
                    </CardDescription>
                  </CardHeader>
                  
                  <CardContent>
                    <p className="text-gray-600 mb-4 line-clamp-3">
                      {venue.description}
                    </p>
                    
                    <div className="space-y-2 mb-4">
                      <div className="flex items-center text-sm text-gray-600">
                        <Phone className="h-4 w-4 mr-2" />
                        {venue.phone}
                      </div>
                      <div className="flex items-center text-sm text-gray-600">
                        <Mail className="h-4 w-4 mr-2" />
                        {venue.email}
                      </div>
                    </div>

                    <div className="mb-4">
                      <h4 className="font-semibold text-sm text-gray-900 mb-2">Amenities</h4>
                      <div className="flex flex-wrap gap-1">
                        {venue.amenities?.slice(0, 3).map((amenity, index) => (
                          <span 
                            key={index}
                            className="bg-blue-100 text-blue-800 text-xs px-2 py-1 rounded"
                          >
                            {amenity}
                          </span>
                        ))}
                        {venue.amenities?.length > 3 && (
                          <span className="text-xs text-gray-500">
                            +{venue.amenities.length - 3} more
                          </span>
                        )}
                      </div>
                    </div>

                    <div className="mb-4">
                      <h4 className="font-semibold text-sm text-gray-900 mb-2">Pricing</h4>
                      <div className="text-sm text-gray-600">
                        <div>Hourly: ${venue.pricing?.hourly_rate || 'N/A'}</div>
                        <div>Daily: ${venue.pricing?.daily_rate || 'N/A'}</div>
                      </div>
                    </div>

                    <div className="flex gap-2">
                      <Link href={`/venues/${venue.id}`} className="flex-1">
                        <Button variant="outline" className="w-full">
                          View Details
                        </Button>
                      </Link>
                      <Link href={`/venues/${venue.id}/book`} className="flex-1">
                        <Button className="w-full">
                          Book Now
                        </Button>
                      </Link>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
          )}
        </div>
      </div>
    </MainLayout>
  );
}