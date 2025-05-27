// frontend/src/app/login/page.tsx
'use client';

import React, { useState } from 'react';
import Link from 'next/link'; // Import Link
// useRouter is no longer needed here as AuthContext handles redirection
import { useAuth } from '@/contexts/AuthContext'; // Import useAuth

const LoginPage: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, isLoading } = useAuth(); // Use login from AuthContext
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);
    try {
      await login(email, password); // Call context login
      // Redirection is handled by AuthContext upon successful login
    } catch (err) {
      console.error('Login failed:', err);
      setError('Login failed. Please check your credentials.'); // Basic error handling
    }
  };

  return (
    <div className="flex items-center justify-center min-h-full py-12 px-4 sm:px-6 lg:px-8">
      <div className="w-full max-w-md space-y-8 bg-[var(--secondary-background)] p-8 rounded-lg shadow-xl">
        <div>
          <h2 className="mt-6 text-center text-3xl font-extrabold text-[var(--accent)]">
            Sign in to your account
          </h2>
        </div>
        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          {error && (
            <div className="bg-red-500 text-white p-3 rounded-md text-sm">
              {error}
            </div>
          )}
          <input type="hidden" name="remember" defaultValue="true" />
          <div className="rounded-md shadow-sm -space-y-px">
            <div>
              <label htmlFor="email-address" className="sr-only">
                Email address
              </label>
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-[var(--border-color)] bg-[var(--background)] text-[var(--foreground)] placeholder-gray-500 focus:outline-none focus:ring-[var(--accent)] focus:border-[var(--accent)] focus:z-10 sm:text-sm rounded-t-md"
                placeholder="Email address"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
              />
            </div>
            <div>
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <input
                id="password"
                name="password"
                type="password"
                autoComplete="current-password"
                required
                className="appearance-none rounded-none relative block w-full px-3 py-2 border border-[var(--border-color)] bg-[var(--background)] text-[var(--foreground)] placeholder-gray-500 focus:outline-none focus:ring-[var(--accent)] focus:border-[var(--accent)] focus:z-10 sm:text-sm rounded-b-md"
                placeholder="Password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
              />
            </div>
          </div>

          {/* <div className="flex items-center justify-between">
            <div className="flex items-center">
              <input
                id="remember-me"
                name="remember-me"
                type="checkbox"
                className="h-4 w-4 text-[var(--accent)] focus:ring-[var(--accent)] border-gray-300 rounded"
              />
              <label htmlFor="remember-me" className="ml-2 block text-sm text-[var(--foreground)]">
                Remember me
              </label>
            </div>

            <div className="text-sm">
              <a href="#" className="font-medium text-[var(--accent)] hover:text-cyan-300">
                Forgot your password?
              </a>
            </div>
          </div> */}

          <div>
            <button
              type="submit"
              disabled={isLoading} // Disable button when loading
              className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-[var(--background)] bg-[var(--accent)] hover:bg-cyan-500 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-offset-gray-800 focus:ring-[var(--accent)] disabled:opacity-50"
            >
              {isLoading ? 'Signing in...' : 'Sign in'}
            </button>
          </div>
          <div className="text-sm text-center">
            <Link href="/register" className="font-medium text-[var(--accent)] hover:text-cyan-300">
              Don&apos;t have an account? Sign up
            </Link>
          </div>
        </form>
      </div>
    </div>
  );
};

export default LoginPage;
