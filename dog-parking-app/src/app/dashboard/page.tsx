'use client';

import { MainLayout } from '@/components/layout/main-layout';
import { ProtectedRoute } from '@/components/auth/protected-route';
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'; // Not needed with inline styles
// import { Button } from '@/components/ui/button'; // Not needed with inline styles
import { useAuth } from '@/contexts/AuthContext';
// import { useOwnerProfile } from '@/hooks/useApi'; // Temporarily disabled due to backend issues
// import { Dog, Calendar, MapPin, Settings } from 'lucide-react'; // Using emojis instead
import Link from 'next/link';

export default function DashboardPage() {
  const { user } = useAuth();
  // const { data: ownerProfile, isLoading, error } = useOwnerProfile(); // Temporarily disabled due to backend issues
  const ownerProfile = null; // Mock for now
  const isLoading = false;
  const error = null;

  return (
    <MainLayout>
      <ProtectedRoute>
        <div style={{
          background: 'linear-gradient(135deg, #fce7f3 0%, #f3e8ff 50%, #fed7aa 100%)',
          minHeight: 'calc(100vh - 64px)',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
        <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '2rem' }}>
          {/* Welcome Header */}
          <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
            <div style={{ 
              fontSize: '4rem',
              marginBottom: '1rem',
              animation: 'wiggle 2s ease-in-out infinite'
            }}>
              🎉
            </div>
            <h1 style={{
              fontSize: '3rem',
              fontWeight: '900',
              marginBottom: '1rem',
              background: 'linear-gradient(45deg, #f59e0b, #ef4444, #ec4899, #8b5cf6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Welcome back, {user?.displayName?.split(' ')[0] || 'Amazing Dog Parent'}! 🐕
            </h1>
            <p style={{ 
              fontSize: '1.25rem',
              color: '#6b7280',
              fontWeight: '500'
            }}>
              Your pup's adventures await! Let's make some tails wag! 🎾
            </p>
          </div>

          {/* Welcome Status */}
          <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
            <div style={{
              backgroundColor: 'white',
              borderRadius: '1.5rem',
              padding: '2rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
              border: '4px solid #10b981',
              display: 'inline-block'
            }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                <div style={{
                  backgroundColor: '#d1fae5',
                  borderRadius: '50%',
                  padding: '1rem',
                  fontSize: '2rem'
                }}>
                  🐕
                </div>
                <div style={{ textAlign: 'left' }}>
                  <h3 style={{ 
                    fontWeight: 'bold', 
                    color: '#065f46',
                    fontSize: '1.25rem',
                    marginBottom: '0.5rem'
                  }}>
                    Account Ready! ✨
                  </h3>
                  <p style={{ color: '#059669', fontSize: '0.875rem' }}>
                    Your Dog Parking adventure starts now!
                  </p>
                </div>
              </div>
            </div>
          </div>

          {/* Quick Actions */}
          <div style={{
            display: 'grid',
            gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))',
            gap: '2rem',
            marginBottom: '3rem'
          }}>
            <Link href="/dogs" style={{ textDecoration: 'none' }}>
              <div style={{
                background: 'linear-gradient(135deg, #fef3c7, #fbbf24)',
                borderRadius: '1.5rem',
                padding: '2rem',
                textAlign: 'center',
                border: '4px solid #fbbf24',
                boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                transform: 'rotate(1deg)'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'rotate(0deg) translateY(-5px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'rotate(1deg)'}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🐕</div>
                <h3 style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: 'bold', 
                  color: '#92400e',
                  marginBottom: '0.5rem'
                }}>
                  My Pups 🌾
                </h3>
                <p style={{ color: '#a16207' }}>
                  Add and manage your furry family!
                </p>
              </div>
            </Link>

            <Link href="/venues" style={{ textDecoration: 'none' }}>
              <div style={{
                background: 'linear-gradient(135deg, #fce7f3, #ec4899)',
                borderRadius: '1.5rem',
                padding: '2rem',
                textAlign: 'center',
                border: '4px solid #ec4899',
                boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                transform: 'rotate(-1deg)'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'rotate(0deg) translateY(-5px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'rotate(-1deg)'}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🏠</div>
                <h3 style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: 'bold', 
                  color: '#9d174d',
                  marginBottom: '0.5rem'
                }}>
                  Find Venues 🎯
                </h3>
                <p style={{ color: '#be185d' }}>
                  Discover amazing care spots nearby!
                </p>
              </div>
            </Link>

            <Link href="/bookings" style={{ textDecoration: 'none' }}>
              <div style={{
                background: 'linear-gradient(135deg, #f3e8ff, #a855f7)',
                borderRadius: '1.5rem',
                padding: '2rem',
                textAlign: 'center',
                border: '4px solid #a855f7',
                boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
                cursor: 'pointer',
                transition: 'transform 0.2s',
                transform: 'rotate(0.5deg)'
              }}
              onMouseOver={(e) => e.currentTarget.style.transform = 'rotate(0deg) translateY(-5px)'}
              onMouseOut={(e) => e.currentTarget.style.transform = 'rotate(0.5deg)'}>
                <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📅</div>
                <h3 style={{ 
                  fontSize: '1.5rem', 
                  fontWeight: 'bold', 
                  color: '#6b21a8',
                  marginBottom: '0.5rem'
                }}>
                  My Bookings ✨
                </h3>
                <p style={{ color: '#7c3aed' }}>
                  Manage all your adventures!
                </p>
              </div>
            </Link>
          </div>

          {/* Getting Started Section */}
          <div style={{
            backgroundColor: 'white',
            borderRadius: '1.5rem',
            padding: '2rem',
            boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
            border: '4px solid #f97316'
          }}>
            <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
              <h2 style={{
                fontSize: '2rem',
                fontWeight: 'bold',
                color: '#1f2937',
                marginBottom: '0.5rem',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.5rem'
              }}>
                ⚙️ Let's Get This Paw-ty Started!
              </h2>
              <p style={{ color: '#6b7280', fontSize: '1rem' }}>
                Complete these fun steps to unleash the full Dog Parking experience! 🚀
              </p>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
              <div style={{
                display: 'flex',
                alignItems: 'center',
                padding: '1.5rem',
                background: 'linear-gradient(135deg, #dbeafe, #3b82f6)',
                borderRadius: '1rem',
                border: '2px solid #3b82f6'
              }}>
                <div style={{
                  backgroundColor: 'white',
                  borderRadius: '50%',
                  padding: '1rem',
                  marginRight: '1rem',
                  fontSize: '1.5rem'
                }}>
                  🐶
                </div>
                <div style={{ flex: 1 }}>
                  <h4 style={{ fontWeight: '600', color: 'white', fontSize: '1.1rem' }}>
                    Add your first furry friend!
                  </h4>
                  <p style={{ fontSize: '0.875rem', color: '#bfdbfe' }}>
                    Create a profile so we know all about your pup
                  </p>
                </div>
                <Link href="/dogs">
                  <button style={{
                    backgroundColor: 'white',
                    color: '#3b82f6',
                    border: 'none',
                    borderRadius: '0.5rem',
                    padding: '0.5rem 1rem',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}>
                    Add Dog 🎆
                  </button>
                </Link>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                padding: '1.5rem',
                background: 'linear-gradient(135deg, #d1fae5, #10b981)',
                borderRadius: '1rem',
                border: '2px solid #10b981'
              }}>
                <div style={{
                  backgroundColor: 'white',
                  borderRadius: '50%',
                  padding: '1rem',
                  marginRight: '1rem',
                  fontSize: '1.5rem'
                }}>
                  🎯
                </div>
                <div style={{ flex: 1 }}>
                  <h4 style={{ fontWeight: '600', color: 'white', fontSize: '1.1rem' }}>
                    Explore pawsome venues!
                  </h4>
                  <p style={{ fontSize: '0.875rem', color: '#a7f3d0' }}>
                    Find the perfect spots for playtime and care
                  </p>
                </div>
                <Link href="/venues">
                  <button style={{
                    backgroundColor: 'white',
                    color: '#10b981',
                    border: 'none',
                    borderRadius: '0.5rem',
                    padding: '0.5rem 1rem',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}>
                    Browse 🔍
                  </button>
                </Link>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                padding: '1.5rem',
                background: 'linear-gradient(135deg, #e9d5ff, #a855f7)',
                borderRadius: '1rem',
                border: '2px solid #a855f7'
              }}>
                <div style={{
                  backgroundColor: 'white',
                  borderRadius: '50%',
                  padding: '1rem',
                  marginRight: '1rem',
                  fontSize: '1.5rem'
                }}>
                  🎉
                </div>
                <div style={{ flex: 1 }}>
                  <h4 style={{ fontWeight: '600', color: 'white', fontSize: '1.1rem' }}>
                    Make your first booking!
                  </h4>
                  <p style={{ fontSize: '0.875rem', color: '#ddd6fe' }}>
                    Schedule daycare, boarding, or grooming fun
                  </p>
                </div>
                <Link href="/venues">
                  <button style={{
                    backgroundColor: 'white',
                    color: '#a855f7',
                    border: 'none',
                    borderRadius: '0.5rem',
                    padding: '0.5rem 1rem',
                    fontWeight: '600',
                    cursor: 'pointer'
                  }}>
                    Book Now 🏆
                  </button>
                </Link>
              </div>
            </div>
          </div>
        </div>
        </div>
      </ProtectedRoute>
      <style jsx>{`
        @keyframes wiggle {
          0% { transform: rotate(-3deg); }
          50% { transform: rotate(3deg); }
          100% { transform: rotate(-3deg); }
        }
      `}</style>
    </MainLayout>
  );
}