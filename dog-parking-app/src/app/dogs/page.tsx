'use client';

import { MainLayout } from '@/components/layout/main-layout';
import { ProtectedRoute } from '@/components/auth/protected-route';
import Link from 'next/link';

export default function DogsPage() {
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
                🐕
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
                My Furry Friends! 🐾
              </h1>
              <p style={{ 
                fontSize: '1.25rem',
                color: '#6b7280',
                fontWeight: '500'
              }}>
                Manage all your pup's profiles and preferences! ✨
              </p>
            </div>

            {/* Coming Soon Card */}
            <div style={{
              backgroundColor: 'white',
              borderRadius: '1.5rem',
              padding: '3rem',
              boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
              border: '4px solid #fbbf24',
              textAlign: 'center',
              margin: '2rem auto',
              maxWidth: '600px'
            }}>
              <div style={{ fontSize: '5rem', marginBottom: '2rem' }}>🚧</div>
              <h2 style={{
                fontSize: '2.5rem',
                fontWeight: 'bold',
                color: '#1f2937',
                marginBottom: '1rem'
              }}>
                Coming Soon!
              </h2>
              <p style={{
                color: '#6b7280',
                fontSize: '1.25rem',
                marginBottom: '2rem',
                lineHeight: '1.6'
              }}>
                We're putting the finishing touches on the most pawsome dog management system ever! 
                Your pups will love their new profiles! 🎉
              </p>
              
              {/* Back to Dashboard */}
              <Link href="/dashboard">
                <button style={{
                  background: 'linear-gradient(45deg, #ec4899, #8b5cf6)',
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