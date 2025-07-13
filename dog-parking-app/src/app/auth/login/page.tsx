'use client';

import { useState, useCallback } from 'react';
import { useAuth } from '@/contexts/AuthContext';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Button } from '@/components/ui/button';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Dog } from 'lucide-react';
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
          // User doesn't exist in backend, register them
          setAuthState({ status: 'registering', error: null, step: 'registration' });
          
          const defaultOwnerData = {
            preferences: {
              notifications: true,
              marketing_emails: false,
              preferred_communication: 'email' as const,
            },
          };

          await registerOwnerMutation.mutateAsync(defaultOwnerData);
          
          // Registration successful
          setAuthState({ status: 'success', error: null, step: 'complete' });
          router.push('/dashboard');
        } else {
          throw new Error(`API error: ${response.status}`);
        }
      } catch (profileError) {
        // If it's just a profile check error, try to register the user
        if (profileError instanceof Error && profileError.message.includes('404')) {
          setAuthState({ status: 'registering', error: null, step: 'registration' });
          
          const defaultOwnerData = {
            preferences: {
              notifications: true,
              marketing_emails: false,
              preferred_communication: 'email' as const,
            },
          };

          await registerOwnerMutation.mutateAsync(defaultOwnerData);
          setAuthState({ status: 'success', error: null, step: 'complete' });
          router.push('/dashboard');
        } else {
          throw profileError;
        }
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
    <div className="min-h-screen flex items-center justify-center bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo and Header */}
        <header className="text-center">
          <div className="flex justify-center mb-6">
            <Dog className="h-12 w-12 text-blue-600" aria-hidden="true" />
          </div>
          <h1 className="text-3xl font-bold text-gray-900 mb-2">
            Welcome back
          </h1>
          <p className="text-sm text-gray-600">
            Sign in to your Dog Parking account
          </p>
        </header>

        {/* Login Card */}
        <Card>
          <CardHeader>
            <CardTitle>Sign In</CardTitle>
            <CardDescription>
              Continue with your Google account to access your dashboard
            </CardDescription>
          </CardHeader>
          
          <CardContent>
            {/* Progress Indicator */}
            {isLoading && (
              <div className="mb-6 p-4 bg-blue-50 rounded-md">
                <div className="flex items-center space-x-3">
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600"></div>
                  <span className="text-sm text-blue-700 font-medium">
                    {getStepDescription()}
                  </span>
                </div>
                <div className="mt-2 w-full bg-blue-200 rounded-full h-2">
                  <div 
                    className={`bg-blue-600 h-2 rounded-full transition-all duration-500 ${
                      authState.step === 'auth' ? 'w-1/4' :
                      authState.step === 'checking' ? 'w-2/4' :
                      authState.step === 'registration' ? 'w-3/4' :
                      'w-full'
                    }`}
                  ></div>
                </div>
              </div>
            )}

            {/* Error Display */}
            {hasError && authState.error && (
              <div 
                className="rounded-md bg-red-50 p-4 mb-6" 
                role="alert"
                aria-live="polite"
              >
                <div className="text-sm text-red-700">
                  {authState.error}
                </div>
              </div>
            )}

            {/* Google Sign-In Button */}
            <Button
              onClick={handleGoogleSignIn}
              disabled={isLoading}
              className="w-full h-12 bg-white border border-gray-300 text-gray-700 hover:bg-gray-50 hover:border-gray-400 focus:ring-2 focus:ring-blue-500 focus:border-blue-500 disabled:opacity-50 disabled:cursor-not-allowed"
              aria-describedby={hasError ? 'auth-error' : undefined}
            >
              <div className="flex items-center justify-center space-x-3">
                {isLoading ? (
                  <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-blue-600" />
                ) : (
                  <svg
                    className="h-5 w-5"
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
                <span className="font-medium">
                  {getLoadingText()}
                </span>
              </div>
            </Button>

            {/* Quick Access Section */}
            <div className="mt-6 pt-6 border-t border-gray-200">
              <h3 className="text-sm font-semibold text-gray-900 mb-3">
                Quick access to:
              </h3>
              <ul className="space-y-2 text-sm text-gray-600">
                <li className="flex items-center">
                  <svg className="h-4 w-4 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Your bookings and reservations
                </li>
                <li className="flex items-center">
                  <svg className="h-4 w-4 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Dog profiles and preferences
                </li>
                <li className="flex items-center">
                  <svg className="h-4 w-4 text-blue-500 mr-2" fill="currentColor" viewBox="0 0 20 20">
                    <path fillRule="evenodd" d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" clipRule="evenodd" />
                  </svg>
                  Booking history and receipts
                </li>
              </ul>
            </div>

            {/* Register Link */}
            <div className="mt-6 text-center">
              <p className="text-sm text-gray-600">
                Don't have an account?{' '}
                <Link 
                  href="/auth/register" 
                  className="font-medium text-blue-600 hover:text-blue-500 focus:outline-none focus:underline transition-colors"
                >
                  Sign up
                </Link>
              </p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  );
}