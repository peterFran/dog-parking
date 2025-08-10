'use client';

import { useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
// import { Button } from '@/components/ui/button'; // Using inline styles instead
// import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'; // Using inline styles instead
// import { Dog } from 'lucide-react'; // Using emojis instead
import { AuthError } from 'firebase/auth';
import { useRegisterOwner, useOwnerProfile } from '@/hooks/useApi';

type AuthenticationState = 'idle' | 'loading' | 'checking' | 'registering' | 'success' | 'error';

interface AuthState {
  status: AuthenticationState;
  error: string | null;
  step: 'auth' | 'checking' | 'registration' | 'complete';
}

const GOOGLE_AUTH_ERROR_MESSAGES: Record<string, string> = {
  'auth/popup-closed-by-user': 'Sign-in was cancelled. Please try again.',
  'auth/popup-blocked': 'Pop-up was blocked. Please allow pop-ups and try again.',
  'auth/cancelled-popup-request': 'Only one sign-in request at a time is allowed.',
  'auth/network-request-failed': 'Network error. Please check your connection and try again.',
  'auth/too-many-requests': 'Too many failed attempts. Please wait and try again later.',
  'auth/user-disabled': 'This account has been disabled. Please contact support.',
  'auth/account-exists-with-different-credential': 'An account already exists with this email using different sign-in method.',
} as const;

const formatAuthError = (error: AuthError): string => {
  return GOOGLE_AUTH_ERROR_MESSAGES[error.code] || 'An unexpected error occurred. Please try again.';
};

export default function LoginPage(): JSX.Element {
  const [authState, setAuthState] = useState<AuthState>({
    status: 'idle',
    error: null,
    step: 'auth',
  });
  
  const { signInWithGoogle, user, getIdToken } = useAuth();
  const router = useRouter();
  const registerOwnerMutation = useRegisterOwner();

  const handleGoogleSignIn = useCallback(async (): Promise<void> => {
    // Prevent multiple concurrent requests
    if (['loading', 'checking', 'registering'].includes(authState.status)) return;

    try {
      // Step 1: Firebase Authentication
      setAuthState({ status: 'loading', error: null, step: 'auth' });
      const authenticatedUser = await signInWithGoogle();
      
      // Step 2: Check if user exists in backend
      setAuthState({ status: 'checking', error: null, step: 'checking' });
      
      try {
        // Get the ID token directly from the authenticated user
        const token = await authenticatedUser.getIdToken();
        
        if (!token) throw new Error('No authentication token available');
        
        // Try to fetch user profile to see if they exist
        setAuthState({ status: 'checking', error: null, step: 'checking' });
        
        try {
          const response = await fetch(`${process.env.NEXT_PUBLIC_API_BASE_URL}/owners/profile`, {
            headers: {
              'Authorization': `Bearer ${token}`,
              'Content-Type': 'application/json',
            },
          });

          if (response.ok) {
            // User exists, proceed to dashboard
            setAuthState({ status: 'success', error: null, step: 'complete' });
            router.push('/dashboard');
          } else if (response.status === 404) {
            // User doesn't exist in backend, try to register them
            setAuthState({ status: 'registering', error: null, step: 'registration' });
            
            const defaultOwnerData = {
              preferences: {
                notifications: true,
                marketing_emails: false,
                preferred_communication: 'email' as const,
              },
            };

            try {
              await registerOwnerMutation.mutateAsync(defaultOwnerData);
              setAuthState({ status: 'success', error: null, step: 'complete' });
              router.push('/dashboard');
            } catch (registerError) {
              // Backend registration failed, but Firebase auth succeeded
              console.warn('Backend registration failed but Firebase auth succeeded:', registerError);
              setAuthState({ status: 'success', error: null, step: 'complete' });
              router.push('/dashboard?setup=incomplete');
            }
          } else {
            throw new Error(`API error: ${response.status}`);
          }
        } catch (apiError) {
          // Backend is not working, but Firebase auth succeeded
          console.warn('Backend API not available, but Firebase auth succeeded:', apiError);
          setAuthState({ status: 'success', error: null, step: 'complete' });
          router.push('/dashboard?setup=incomplete');
        }
      } catch (tokenError) {
        throw tokenError;
      }
    } catch (error) {
      console.error('Login flow failed:', error);
      
      let errorMessage: string;
      
      // Check if it's a Firebase auth error
      if (error && typeof error === 'object' && 'code' in error) {
        const authError = error as AuthError;
        errorMessage = formatAuthError(authError);
      } 
      // Check if it's an API error
      else if (error instanceof Error) {
        errorMessage = `Login failed: ${error.message}`;
      } else {
        errorMessage = 'An unexpected error occurred during login. Please try again.';
      }
      
      setAuthState({ 
        status: 'error', 
        error: errorMessage,
        step: 'auth'
      });
    }
  }, [signInWithGoogle, router, getIdToken, registerOwnerMutation, authState.status]);

  const isLoading = ['loading', 'checking', 'registering'].includes(authState.status);
  const hasError = authState.status === 'error';
  
  const getLoadingText = (): string => {
    switch (authState.status) {
      case 'loading':
        return 'Signing in with Google...';
      case 'checking':
        return 'Checking your account...';
      case 'registering':
        return 'Setting up your account...';
      default:
        return 'Continue with Google';
    }
  };

  const getStepDescription = (): string => {
    switch (authState.step) {
      case 'auth':
        return 'Authenticating with Google';
      case 'checking':
        return 'Verifying your account status';
      case 'registration':
        return 'Setting up your Dog Parking account';
      case 'complete':
        return 'Login complete!';
      default:
        return '';
    }
  };

  return (
    <div className="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8" style={{
      background: 'linear-gradient(135deg, #fce7f3 0%, #f3e8ff 50%, #fed7aa 100%)',
      fontFamily: 'system-ui, -apple-system, sans-serif'
    }}>
      <div className="max-w-md w-full space-y-8">
        {/* Logo and Header */}
        <header className="text-center">
          <div className="flex justify-center mb-6" style={{ 
            fontSize: '4rem',
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
            🎉 Welcome Back! 🎉
          </h1>
          <p style={{ 
            fontSize: '1.25rem',
            color: '#6b7280',
            marginBottom: '2rem',
            fontWeight: '500'
          }}>
            Your pups missed you! Let's get you signed in! 🐾
          </p>
        </header>

        {/* Login Card */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '1.5rem',
          padding: '2rem',
          boxShadow: '0 20px 25px -5px rgba(0, 0, 0, 0.1), 0 10px 10px -5px rgba(0, 0, 0, 0.04)',
          border: '4px solid #10b981'
        }}>
          <div style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
            <h2 style={{
              fontSize: '2rem',
              fontWeight: 'bold',
              color: '#1f2937',
              marginBottom: '0.5rem'
            }}>
              Sign In 🚪
            </h2>
            <p style={{ color: '#6b7280', fontSize: '1rem' }}>
              One click and you're back in the pack! 🌟
            </p>
          </div>
          
          <div>
            {/* Progress Indicator */}
            {isLoading && (
              <div style={{
                marginBottom: '1.5rem',
                padding: '1rem',
                background: 'linear-gradient(135deg, #d1fae5, #10b981)',
                borderRadius: '1rem',
                border: '2px solid #10b981'
              }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
                  <div style={{
                    width: '20px',
                    height: '20px',
                    border: '2px solid white',
                    borderTop: '2px solid transparent',
                    borderRadius: '50%',
                    animation: 'spin 1s linear infinite'
                  }}></div>
                  <span style={{ 
                    fontSize: '0.875rem',
                    color: 'white',
                    fontWeight: '600'
                  }}>
                    🐕 {getStepDescription()}
                  </span>
                </div>
                <div style={{
                  marginTop: '0.5rem',
                  width: '100%',
                  backgroundColor: '#10b981',
                  borderRadius: '9999px',
                  height: '8px'
                }}>
                  <div style={{
                    backgroundColor: 'white',
                    height: '8px',
                    borderRadius: '9999px',
                    transition: 'all 0.5s',
                    width: authState.step === 'auth' ? '25%' :
                           authState.step === 'checking' ? '50%' :
                           authState.step === 'registration' ? '75%' : '100%'
                  }}></div>
                </div>
              </div>
            )}

            {/* Error Display */}
            {hasError && authState.error && (
              <div style={{
                borderRadius: '1rem',
                background: 'linear-gradient(135deg, #fef2f2, #fee2e2)',
                padding: '1rem',
                marginBottom: '1.5rem',
                border: '2px solid #fecaca'
              }} role="alert" aria-live="polite">
                <div style={{ 
                  fontSize: '0.875rem', 
                  color: '#dc2626',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem'
                }}>
                  😿 {authState.error}
                </div>
              </div>
            )}

            {/* Google Sign-In Button */}
            <button
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              style={{
                width: '100%',
                height: '3.5rem',
                backgroundColor: 'white',
                border: '3px solid #e5e7eb',
                borderRadius: '1rem',
                color: '#374151',
                fontSize: '1.1rem',
                fontWeight: '600',
                cursor: isLoading ? 'not-allowed' : 'pointer',
                opacity: isLoading ? 0.5 : 1,
                boxShadow: '0 10px 15px -3px rgba(0, 0, 0, 0.1), 0 4px 6px -2px rgba(0, 0, 0, 0.05)',
                transition: 'all 0.2s',
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                gap: '0.75rem'
              }}
              onMouseOver={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.backgroundColor = '#f9fafb';
                  e.currentTarget.style.borderColor = '#d1d5db';
                  e.currentTarget.style.transform = 'translateY(-2px)';
                }
              }}
              onMouseOut={(e) => {
                if (!isLoading) {
                  e.currentTarget.style.backgroundColor = 'white';
                  e.currentTarget.style.borderColor = '#e5e7eb';
                  e.currentTarget.style.transform = 'translateY(0)';
                }
              }}
              aria-describedby={hasError ? 'auth-error' : undefined}
            >
              {isLoading ? (
                <div style={{
                  width: '20px',
                  height: '20px',
                  border: '2px solid #10b981',
                  borderTop: '2px solid transparent',
                  borderRadius: '50%',
                  animation: 'spin 1s linear infinite'
                }} />
              ) : (
                <svg
                  style={{ height: '20px', width: '20px' }}
                  viewBox="0 0 24 24"
                  aria-hidden="true"
                >
                  <path
                    fill="#4285F4"
                    d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                  />
                  <path
                    fill="#34A853"
                    d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                  />
                  <path
                    fill="#FBBC05"
                    d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                  />
                  <path
                    fill="#EA4335"
                    d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                  />
                </svg>
              )}
              <span>
                {getLoadingText()}
              </span>
            </button>

            {/* Quick Access Section */}
            <div style={{
              marginTop: '1.5rem',
              paddingTop: '1.5rem',
              borderTop: '2px solid #f3f4f6'
            }}>
              <h3 style={{
                fontSize: '1.125rem',
                fontWeight: 'bold',
                color: '#1f2937',
                marginBottom: '1rem',
                textAlign: 'center'
              }}>
                🚀 Jump back into:
              </h3>
              <div style={{
                display: 'grid',
                gap: '0.75rem'
              }}>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.75rem',
                  backgroundColor: '#fef3c7',
                  borderRadius: '0.75rem',
                  border: '2px solid #fbbf24'
                }}>
                  <span style={{ fontSize: '1.25rem', marginRight: '0.75rem' }}>📅</span>
                  <span style={{ color: '#92400e', fontWeight: '500' }}>
                    Your bookings and adventures
                  </span>
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.75rem',
                  backgroundColor: '#fce7f3',
                  borderRadius: '0.75rem',
                  border: '2px solid #ec4899'
                }}>
                  <span style={{ fontSize: '1.25rem', marginRight: '0.75rem' }}>🐕‍🦺</span>
                  <span style={{ color: '#9d174d', fontWeight: '500' }}>
                    Your furry friend profiles
                  </span>
                </div>
                <div style={{
                  display: 'flex',
                  alignItems: 'center',
                  padding: '0.75rem',
                  backgroundColor: '#f3e8ff',
                  borderRadius: '0.75rem',
                  border: '2px solid #a855f7'
                }}>
                  <span style={{ fontSize: '1.25rem', marginRight: '0.75rem' }}>📊</span>
                  <span style={{ color: '#6b21a8', fontWeight: '500' }}>
                    History and tail-wagging moments
                  </span>
                </div>
              </div>
            </div>

            {/* Register Link */}
            <div style={{ marginTop: '1.5rem', textAlign: 'center' }}>
              <p style={{ fontSize: '0.875rem', color: '#6b7280' }}>
                New to the pack?{' '}
                <Link 
                  href="/auth/register" 
                  style={{
                    fontWeight: '600',
                    color: '#10b981',
                    textDecoration: 'none'
                  }}
                  onMouseOver={(e) => e.currentTarget.style.textDecoration = 'underline'}
                  onMouseOut={(e) => e.currentTarget.style.textDecoration = 'none'}
                >
                  Join us here! 🎉
                </Link>
              </p>
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
        
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </div>
  );
}