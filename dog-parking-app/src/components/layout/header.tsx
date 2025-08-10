'use client';

import Link from 'next/link';
import { useAuth } from '@/contexts/AuthContext';
// import { Button } from '@/components/ui/button'; // Using inline styles instead
// import { Dog, Menu, User, LogOut } from 'lucide-react'; // Using emojis instead
import { useState } from 'react';

export function Header() {
  const { user, signOut } = useAuth();
  const [mobileMenuOpen, setMobileMenuOpen] = useState(false);

  const handleSignOut = async () => {
    try {
      await signOut();
    } catch (error) {
      console.error('Sign out error:', error);
    }
  };

  return (
    <header style={{
      backgroundColor: 'white',
      boxShadow: '0 4px 6px -1px rgba(0, 0, 0, 0.1), 0 2px 4px -1px rgba(0, 0, 0, 0.06)',
      borderBottom: '4px solid #fbbf24',
      position: 'sticky',
      top: 0,
      zIndex: 50
    }}>
      <div style={{
        maxWidth: '80rem',
        margin: '0 auto',
        padding: '0 2rem'
      }}>
        <div style={{
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          height: '4rem'
        }}>
          {/* Logo */}
          <Link href="/" style={{
            display: 'flex',
            alignItems: 'center',
            gap: '0.5rem',
            textDecoration: 'none'
          }}>
            <span style={{ fontSize: '2rem' }}>🐕</span>
            <span style={{
              fontSize: '1.5rem',
              fontWeight: 'bold',
              background: 'linear-gradient(45deg, #f59e0b, #ef4444, #ec4899, #8b5cf6)',
              WebkitBackgroundClip: 'text',
              WebkitTextFillColor: 'transparent',
              backgroundClip: 'text'
            }}>
              Dog Parking
            </span>
          </Link>

          {/* Desktop Navigation */}
          <nav style={{
            display: 'flex',
            alignItems: 'center',
            gap: '2rem'
          }}>
            <Link href="/venues" style={{
              color: '#6b7280',
              textDecoration: 'none',
              fontWeight: '600',
              padding: '0.5rem 1rem',
              borderRadius: '0.5rem',
              transition: 'all 0.2s'
            }}
            onMouseOver={(e) => {
              e.currentTarget.style.backgroundColor = '#fef3c7';
              e.currentTarget.style.color = '#92400e';
            }}
            onMouseOut={(e) => {
              e.currentTarget.style.backgroundColor = 'transparent';
              e.currentTarget.style.color = '#6b7280';
            }}>
              🏠 Find Venues
            </Link>
            {user && (
              <>
                <Link href="/dashboard" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  fontWeight: '600',
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#fce7f3';
                  e.currentTarget.style.color = '#9d174d';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  📊 Dashboard
                </Link>
                <Link href="/dogs" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  fontWeight: '600',
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#f3e8ff';
                  e.currentTarget.style.color = '#6b21a8';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  🐶 My Dogs
                </Link>
                <Link href="/bookings" style={{
                  color: '#6b7280',
                  textDecoration: 'none',
                  fontWeight: '600',
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#fed7aa';
                  e.currentTarget.style.color = '#9a3412';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  📅 Bookings
                </Link>
              </>
            )}
          </nav>

          {/* Auth Actions */}
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: '1rem'
          }}>
            {user ? (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              }}>
                <Link href="/profile">
                  <button style={{
                    backgroundColor: 'transparent',
                    border: 'none',
                    color: '#6b7280',
                    cursor: 'pointer',
                    padding: '0.5rem 1rem',
                    borderRadius: '0.5rem',
                    fontWeight: '600',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.5rem',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = '#f3e8ff';
                    e.currentTarget.style.color = '#6b21a8';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.color = '#6b7280';
                  }}>
                    👤 Profile
                  </button>
                </Link>
                <button onClick={handleSignOut} style={{
                  backgroundColor: 'transparent',
                  border: 'none',
                  color: '#6b7280',
                  cursor: 'pointer',
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  fontWeight: '600',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  transition: 'all 0.2s'
                }}
                onMouseOver={(e) => {
                  e.currentTarget.style.backgroundColor = '#fee2e2';
                  e.currentTarget.style.color = '#dc2626';
                }}
                onMouseOut={(e) => {
                  e.currentTarget.style.backgroundColor = 'transparent';
                  e.currentTarget.style.color = '#6b7280';
                }}>
                  👋 Sign Out
                </button>
              </div>
            ) : (
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: '1rem'
              }}>
                <Link href="/auth/login">
                  <button style={{
                    backgroundColor: 'transparent',
                    border: '2px solid #e5e7eb',
                    color: '#6b7280',
                    cursor: 'pointer',
                    padding: '0.5rem 1.5rem',
                    borderRadius: '0.75rem',
                    fontWeight: '600',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.backgroundColor = '#f9fafb';
                    e.currentTarget.style.borderColor = '#d1d5db';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.backgroundColor = 'transparent';
                    e.currentTarget.style.borderColor = '#e5e7eb';
                  }}>
                    Sign In
                  </button>
                </Link>
                <Link href="/auth/register">
                  <button style={{
                    background: 'linear-gradient(45deg, #ec4899, #8b5cf6)',
                    border: 'none',
                    color: 'white',
                    cursor: 'pointer',
                    padding: '0.5rem 1.5rem',
                    borderRadius: '0.75rem',
                    fontWeight: '600',
                    boxShadow: '0 4px 14px 0 rgba(0, 0, 0, 0.2)',
                    transition: 'all 0.2s'
                  }}
                  onMouseOver={(e) => {
                    e.currentTarget.style.transform = 'translateY(-2px)';
                    e.currentTarget.style.boxShadow = '0 8px 25px 0 rgba(0, 0, 0, 0.3)';
                  }}
                  onMouseOut={(e) => {
                    e.currentTarget.style.transform = 'translateY(0)';
                    e.currentTarget.style.boxShadow = '0 4px 14px 0 rgba(0, 0, 0, 0.2)';
                  }}>
                    🚀 Get Started
                  </button>
                </Link>
              </div>
            )}
          </div>

          {/* Mobile menu button */}
          <div style={{
            display: mobileMenuOpen ? 'block' : 'none'
          }}>
            <button
              onClick={() => setMobileMenuOpen(!mobileMenuOpen)}
              style={{
                backgroundColor: 'transparent',
                border: 'none',
                cursor: 'pointer',
                fontSize: '1.5rem'
              }}
            >
              {mobileMenuOpen ? '❌' : '☰'}
            </button>
          </div>
        </div>

        {/* Mobile Navigation */}
        {mobileMenuOpen && (
          <div style={{
            borderTop: '2px solid #fbbf24',
            paddingTop: '1rem',
            paddingBottom: '1rem'
          }}>
            <div style={{
              display: 'flex',
              flexDirection: 'column',
              gap: '0.5rem'
            }}>
              <Link
                href="/venues"
                style={{
                  display: 'block',
                  padding: '0.75rem 1rem',
                  color: '#6b7280',
                  textDecoration: 'none',
                  borderRadius: '0.5rem'
                }}
                onClick={() => setMobileMenuOpen(false)}
                onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#fef3c7'}
                onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
              >
                🏠 Find Venues
              </Link>
              {user ? (
                <>
                  <Link
                    href="/dashboard"
                    style={{
                      display: 'block',
                      padding: '0.75rem 1rem',
                      color: '#6b7280',
                      textDecoration: 'none',
                      borderRadius: '0.5rem'
                    }}
                    onClick={() => setMobileMenuOpen(false)}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#fce7f3'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    📊 Dashboard
                  </Link>
                  <Link
                    href="/dogs"
                    style={{
                      display: 'block',
                      padding: '0.75rem 1rem',
                      color: '#6b7280',
                      textDecoration: 'none',
                      borderRadius: '0.5rem'
                    }}
                    onClick={() => setMobileMenuOpen(false)}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f3e8ff'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    🐶 My Dogs
                  </Link>
                  <Link
                    href="/bookings"
                    style={{
                      display: 'block',
                      padding: '0.75rem 1rem',
                      color: '#6b7280',
                      textDecoration: 'none',
                      borderRadius: '0.5rem'
                    }}
                    onClick={() => setMobileMenuOpen(false)}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#fed7aa'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    📅 Bookings
                  </Link>
                  <Link
                    href="/profile"
                    style={{
                      display: 'block',
                      padding: '0.75rem 1rem',
                      color: '#6b7280',
                      textDecoration: 'none',
                      borderRadius: '0.5rem'
                    }}
                    onClick={() => setMobileMenuOpen(false)}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f3e8ff'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    👤 Profile
                  </Link>
                  <button
                    onClick={() => {
                      handleSignOut();
                      setMobileMenuOpen(false);
                    }}
                    style={{
                      display: 'block',
                      width: '100%',
                      textAlign: 'left',
                      padding: '0.75rem 1rem',
                      color: '#6b7280',
                      backgroundColor: 'transparent',
                      border: 'none',
                      borderRadius: '0.5rem',
                      cursor: 'pointer'
                    }}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#fee2e2'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    👋 Sign Out
                  </button>
                </>
              ) : (
                <>
                  <Link
                    href="/auth/login"
                    style={{
                      display: 'block',
                      padding: '0.75rem 1rem',
                      color: '#6b7280',
                      textDecoration: 'none',
                      borderRadius: '0.5rem'
                    }}
                    onClick={() => setMobileMenuOpen(false)}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/auth/register"
                    style={{
                      display: 'block',
                      padding: '0.75rem 1rem',
                      color: '#6b7280',
                      textDecoration: 'none',
                      borderRadius: '0.5rem'
                    }}
                    onClick={() => setMobileMenuOpen(false)}
                    onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f3e8ff'}
                    onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                  >
                    🚀 Get Started
                  </Link>
                </>
              )}
            </div>
          </div>
        )}
      </div>
    </header>
  );
}