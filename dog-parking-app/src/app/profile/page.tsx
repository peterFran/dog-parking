'use client';

import { MainLayout } from '@/components/layout/main-layout';
import { ProtectedRoute } from '@/components/auth/protected-route';
import { useAuth } from '@/contexts/AuthContext';
import Link from 'next/link';

export default function ProfilePage() {
  const { user } = useAuth();

  return (
    <MainLayout>
      <ProtectedRoute>
        <div style={{
          background: 'linear-gradient(135deg, #fce7f3 0%, #f3e8ff 50%, #fed7aa 100%)',
          minHeight: 'calc(100vh - 64px)',
          fontFamily: 'system-ui, -apple-system, sans-serif'
        }}>
          <div style={{ maxWidth: '80rem', margin: '0 auto', padding: '2rem' }}>
            {/* Header */}
            <div style={{ marginBottom: '2rem', textAlign: 'center' }}>
              <div style={{ 
                fontSize: '4rem',
                marginBottom: '1rem',
                animation: 'wiggle 2s ease-in-out infinite'
              }}>
                👤
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
                My Profile! 🌟
              </h1>
              <p style={{ 
                fontSize: '1.25rem',
                color: '#6b7280',
                fontWeight: '500'
              }}>
                Hey there, {user?.displayName?.split(' ')[0] || 'Amazing Dog Parent'}! 👋
              </p>
            </div>

            {/* Profile Info Card */}
            <div style={{
              backgroundColor: 'white',
              borderRadius: '1.5rem',
              padding: '2rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
              border: '4px solid #ec4899',
              margin: '2rem auto',
              maxWidth: '600px'
            }}>
              {/* User Info */}
              <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
                {user?.photoURL && (
                  <img 
                    src={user.photoURL} 
                    alt="Profile"
                    style={{
                      width: '100px',
                      height: '100px',
                      borderRadius: '50%',
                      marginBottom: '1rem',
                      border: '4px solid #ec4899'
                    }}
                  />
                )}
                <h2 style={{
                  fontSize: '2rem',
                  fontWeight: 'bold',
                  color: '#1f2937',
                  marginBottom: '0.5rem'
                }}>
                  {user?.displayName || 'Dog Parent Extraordinaire'}
                </h2>
                <p style={{ color: '#6b7280', fontSize: '1rem' }}>
                  {user?.email}
                </p>
              </div>

              {/* Profile Stats */}
              <div style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))',
                gap: '1rem',
                marginBottom: '2rem'
              }}>
                <div style={{
                  backgroundColor: '#fef3c7',
                  padding: '1.5rem',
                  borderRadius: '1rem',
                  textAlign: 'center',
                  border: '2px solid #fbbf24'
                }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>🐕</div>
                  <div style={{ color: '#92400e', fontSize: '2rem', fontWeight: 'bold' }}>0</div>
                  <div style={{ color: '#a16207', fontSize: '0.875rem' }}>Registered Pups</div>
                </div>
                <div style={{
                  backgroundColor: '#fce7f3',
                  padding: '1.5rem',
                  borderRadius: '1rem',
                  textAlign: 'center',
                  border: '2px solid #ec4899'
                }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>📅</div>
                  <div style={{ color: '#9d174d', fontSize: '2rem', fontWeight: 'bold' }}>0</div>
                  <div style={{ color: '#be185d', fontSize: '0.875rem' }}>Total Bookings</div>
                </div>
                <div style={{
                  backgroundColor: '#f3e8ff',
                  padding: '1.5rem',
                  borderRadius: '1rem',
                  textAlign: 'center',
                  border: '2px solid #a855f7'
                }}>
                  <div style={{ fontSize: '2.5rem', marginBottom: '0.5rem' }}>⭐</div>
                  <div style={{ color: '#6b21a8', fontSize: '2rem', fontWeight: 'bold' }}>New</div>
                  <div style={{ color: '#7c3aed', fontSize: '0.875rem' }}>Member Status</div>
                </div>
              </div>

              {/* Coming Soon Features */}
              <div style={{
                backgroundColor: '#fed7aa',
                padding: '2rem',
                borderRadius: '1rem',
                textAlign: 'center',
                border: '2px solid #f97316',
                marginBottom: '2rem'
              }}>
                <h3 style={{
                  fontSize: '1.5rem',
                  fontWeight: 'bold',
                  color: '#9a3412',
                  marginBottom: '1rem'
                }}>
                  🚧 Profile Features Coming Soon!
                </h3>
                <p style={{ color: '#c2410c', marginBottom: '1rem' }}>
                  We're building amazing profile customization features!
                </p>
                <div style={{ fontSize: '0.875rem', color: '#ea580c' }}>
                  • Notification preferences<br/>
                  • Emergency contacts<br/>
                  • Billing & payment methods<br/>
                  • Account settings
                </div>
              </div>
              
              {/* Back to Dashboard */}
              <div style={{ textAlign: 'center' }}>
                <Link href="/dashboard">
                  <button style={{
                    background: 'linear-gradient(45deg, #ec4899, #f97316)',
                    border: 'none',
                    color: 'white',
                    cursor: 'pointer',
                    padding: '1rem 2rem',
                    borderRadius: '1rem',
                    fontWeight: '600',
                    fontSize: '1.1rem',
                    boxShadow: '0 8px 25px 0 rgba(0, 0, 0, 0.3)',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 12px 30px 0 rgba(0, 0, 0, 0.4)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 8px 25px 0 rgba(0, 0, 0, 0.3)';
                  }}>
                    🏠 Back to Dashboard
                  </button>
                </Link>
              </div>
            </div>
          </div>
        </div>

        <style jsx>{`
          @keyframes wiggle {
            0% { transform: rotate(-3deg); }
            50% { transform: rotate(3deg); }
            100% { transform: rotate(-3deg); }
          }
        `}</style>
      </ProtectedRoute>
    </MainLayout>
  );
}