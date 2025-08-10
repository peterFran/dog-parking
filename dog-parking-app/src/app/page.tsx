'use client';

import Link from 'next/link';

export default function Home() {
  return (
    <div className="min-h-screen" style={{ 
      background: 'linear-gradient(135deg, #fce7f3 0%, #f3e8ff 50%, #fed7aa 100%)',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      {/* Header */}
      <header className="p-6" style={{ backgroundColor: 'white', boxShadow: '0 2px 10px rgba(0,0,0,0.1)' }}>
        <div className="flex justify-between items-center max-w-7xl mx-auto">
          <div className="flex items-center space-x-3">
            <span style={{ fontSize: '2rem' }}>🐕</span>
            <h1 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#1f2937' }}>Dog Parking</h1>
          </div>
          <div className="space-x-4">
            <Link href="/venues" style={{ 
              color: '#6b7280',
              textDecoration: 'none',
              padding: '0.5rem 1rem'
            }}>
              Find Venues
            </Link>
            <Link href="/auth/login" style={{
              color: '#6b7280',
              textDecoration: 'none',
              padding: '0.5rem 1rem'
            }}>
              Sign In
            </Link>
            <Link href="/auth/register" style={{
              backgroundColor: '#3b82f6',
              color: 'white',
              textDecoration: 'none',
              padding: '0.75rem 1.5rem',
              borderRadius: '0.5rem',
              fontWeight: '600'
            }}>
              Get Started
            </Link>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <section style={{ padding: '6rem 1.5rem', textAlign: 'center' }}>
        <div style={{ maxWidth: '64rem', margin: '0 auto' }}>
          {/* Big Dog Emoji */}
          <div style={{ 
            fontSize: '6rem', 
            marginBottom: '2rem',
            animation: 'wiggle 2s ease-in-out infinite'
          }}>
            🐕
          </div>
          
          <h1 style={{ 
            fontSize: '4rem',
            fontWeight: '900',
            marginBottom: '2rem',
            lineHeight: '1.1',
            background: 'linear-gradient(45deg, #f59e0b, #ef4444, #ec4899, #8b5cf6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            Pawsome<br />Dog Parking!
          </h1>
          
          <p style={{ 
            fontSize: '2rem', 
            color: '#374151',
            marginBottom: '3rem',
            fontWeight: '500'
          }}>
            🎾 Your pup's new favorite hangout spot! 🎾<br />
            <span style={{ fontSize: '1.25rem', color: '#6b7280' }}>
              Flexible subscriptions starting at just £20/hour
            </span>
          </p>
          
          {/* Price Badges */}
          <div style={{ 
            display: 'flex', 
            justifyContent: 'center', 
            gap: '1rem',
            marginBottom: '3rem',
            flexWrap: 'wrap'
          }}>
            <div style={{
              backgroundColor: 'white',
              padding: '1rem 1.5rem',
              borderRadius: '2rem',
              border: '4px solid #fbbf24',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              transform: 'rotate(2deg)'
            }}>
              <span style={{ color: '#d97706', fontWeight: 'bold' }}>🐾 Puppy Package: £100/mo</span>
            </div>
            <div style={{
              backgroundColor: 'white',
              padding: '1rem 1.5rem',
              borderRadius: '2rem',
              border: '4px solid #ec4899',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              transform: 'rotate(-1deg)'
            }}>
              <span style={{ color: '#be185d', fontWeight: 'bold' }}>🌟 Good Dog: £200/mo</span>
            </div>
            <div style={{
              backgroundColor: 'white',
              padding: '1rem 1.5rem',
              borderRadius: '2rem',
              border: '4px solid #a855f7',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              transform: 'rotate(1deg)'
            }}>
              <span style={{ color: '#7c3aed', fontWeight: 'bold' }}>👑 Top Dog: £380/mo</span>
            </div>
          </div>
          
          <div style={{ display: 'flex', gap: '1.5rem', justifyContent: 'center' }}>
            <Link href="/venues" style={{
              background: 'linear-gradient(45deg, #ec4899, #f97316)',
              color: 'white',
              textDecoration: 'none',
              padding: '1rem 2rem',
              fontSize: '1.25rem',
              fontWeight: 'bold',
              borderRadius: '1rem',
              boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
              border: '4px solid white'
            }}>
              🗺️ Find My Pack!
            </Link>
            <Link href="/auth/register" style={{
              backgroundColor: 'white',
              color: '#7c3aed',
              textDecoration: 'none',
              padding: '1rem 2rem',
              fontSize: '1.25rem',
              fontWeight: 'bold',
              borderRadius: '1rem',
              boxShadow: '0 10px 25px rgba(0,0,0,0.2)',
              border: '4px solid #a855f7'
            }}>
              🚀 Start Playing!
            </Link>
          </div>
        </div>
      </section>

      {/* Features */}
      <section style={{ padding: '4rem 1.5rem', backgroundColor: 'white' }}>
        <div style={{ maxWidth: '64rem', margin: '0 auto', textAlign: 'center' }}>
          <h2 style={{ 
            fontSize: '3rem',
            fontWeight: '900',
            marginBottom: '3rem',
            background: 'linear-gradient(45deg, #f59e0b, #ef4444, #ec4899, #8b5cf6)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            backgroundClip: 'text'
          }}>
            Why We're Paw-sitively Amazing!
          </h2>
          
          <div style={{ 
            display: 'grid', 
            gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', 
            gap: '2rem' 
          }}>
            <div style={{
              background: 'linear-gradient(135deg, #fef3c7, #fbbf24)',
              padding: '2rem',
              borderRadius: '1.5rem',
              border: '4px solid #fbbf24',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>⚡</div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#92400e', marginBottom: '1rem' }}>
                Flex-a-Pup Hours!
              </h3>
              <p style={{ color: '#a16207' }}>
                Buy hours in bulk, use them whenever! No stress, no mess! 🕒
              </p>
            </div>
            
            <div style={{
              background: 'linear-gradient(135deg, #fce7f3, #ec4899)',
              padding: '2rem',
              borderRadius: '1.5rem',
              border: '4px solid #ec4899',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🛡️</div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#9d174d', marginBottom: '1rem' }}>
                Super Safe Spots!
              </h3>
              <p style={{ color: '#be185d' }}>
                QR codes + human heroes = maximum security! 💖
              </p>
            </div>
            
            <div style={{
              background: 'linear-gradient(135deg, #f3e8ff, #a855f7)',
              padding: '2rem',
              borderRadius: '1.5rem',
              border: '4px solid #a855f7',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>🎉</div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#6b21a8', marginBottom: '1rem' }}>
                Paw-ty Central!
              </h3>
              <p style={{ color: '#7c3aed' }}>
                Supervised play dates every day! 🐾
              </p>
            </div>
            
            <div style={{
              background: 'linear-gradient(135deg, #fed7aa, #f97316)',
              padding: '2rem',
              borderRadius: '1.5rem',
              border: '4px solid #f97316',
              boxShadow: '0 10px 25px rgba(0,0,0,0.1)',
              textAlign: 'center'
            }}>
              <div style={{ fontSize: '4rem', marginBottom: '1rem' }}>📸</div>
              <h3 style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#9a3412', marginBottom: '1rem' }}>
                Paparazzi Pics!
              </h3>
              <p style={{ color: '#c2410c' }}>
                Adorable updates all day long! 📱
              </p>
            </div>
          </div>
        </div>
      </section>

      {/* Final CTA */}
      <section style={{ 
        padding: '4rem 1.5rem',
        background: 'linear-gradient(135deg, #ec4899, #8b5cf6, #f97316)',
        textAlign: 'center',
        color: 'white'
      }}>
        <div style={{ maxWidth: '48rem', margin: '0 auto' }}>
          <div style={{ fontSize: '5rem', marginBottom: '2rem' }}>🎉</div>
          <h2 style={{ 
            fontSize: '3rem',
            fontWeight: '900',
            marginBottom: '2rem'
          }}>
            Ready to Make Your Pup's Day?
          </h2>
          <p style={{ fontSize: '1.5rem', marginBottom: '3rem', opacity: 0.9 }}>
            🚀 Join the pack of happy dogs and stress-free humans! 🚀
          </p>
          
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <Link href="/auth/register" style={{
              backgroundColor: 'white',
              color: '#7c3aed',
              textDecoration: 'none',
              padding: '1rem 2rem',
              fontSize: '1.5rem',
              fontWeight: 'bold',
              borderRadius: '1.5rem',
              boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
              border: '4px solid #fbbf24'
            }}>
              🎾 Let's Play!
            </Link>
            <Link href="/venues" style={{
              backgroundColor: 'transparent',
              color: 'white',
              textDecoration: 'none',
              padding: '1rem 2rem',
              fontSize: '1.5rem',
              fontWeight: 'bold',
              borderRadius: '1.5rem',
              boxShadow: '0 10px 25px rgba(0,0,0,0.3)',
              border: '4px solid white'
            }}>
              🗺️ Find My Spot!
            </Link>
          </div>
        </div>
      </section>

      <style jsx>{`
        @keyframes wiggle {
          0% { transform: rotate(-3deg); }
          50% { transform: rotate(3deg); }
          100% { transform: rotate(-3deg); }
        }
      `}</style>
    </div>
  );
}