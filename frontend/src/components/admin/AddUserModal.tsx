// frontend/src/components/admin/AddUserModal.tsx
'use client';

import React, { useState } from 'react';

interface AddUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  // Updated userData structure for onAddUser callback
  onAddUser: (userData: { email: string; username: string; password: string; isAdmin: boolean; }) => void;
}

const AddUserModal: React.FC<AddUserModalProps> = ({ isOpen, onClose, onAddUser }) => {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState(''); // Added username state
  const [password, setPassword] = useState('');
  const [isAdmin, setIsAdmin] = useState(false); // Changed from role to isAdmin (boolean)

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !username || !password) { // Added username to validation
        alert('Email, Username, and Password are required.');
        return;
    }
    // Pass all required fields to onAddUser
    onAddUser({ email, username, password, isAdmin });
    setEmail('');
    setUsername(''); // Reset username
    setPassword('');
    setIsAdmin(false); // Reset isAdmin to default
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-[var(--secondary-background)] p-8 rounded-lg shadow-xl w-full max-w-md text-[var(--foreground)]">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-[var(--accent)]">Add New User</h2>
          <button onClick={onClose} className="text-[var(--foreground)] hover:text-[var(--accent)] text-2xl">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="username" className="block text-sm font-medium mb-1">Username</label>
            <input
              type="text"
              id="username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full p-3 bg-[var(--background)] border border-[var(--border-color)] rounded-md focus:ring-[var(--accent)] focus:border-[var(--accent)]"
            />
          </div>
          <div>
            <label htmlFor="email" className="block text-sm font-medium mb-1">Email Address</label>
            <input
              type="email"
              id="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full p-3 bg-[var(--background)] border border-[var(--border-color)] rounded-md focus:ring-[var(--accent)] focus:border-[var(--accent)]"
            />
          </div>
          <div>
            <label htmlFor="password" className="block text-sm font-medium mb-1">Password</label>
            <input
              type="password"
              id="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className="w-full p-3 bg-[var(--background)] border border-[var(--border-color)] rounded-md focus:ring-[var(--accent)] focus:border-[var(--accent)]"
            />
          </div>
          <div>
            <label htmlFor="isAdmin" className="block text-sm font-medium mb-1">Administrator</label>
            <select
              id="isAdmin"
              value={isAdmin ? 'true' : 'false'}
              onChange={(e) => setIsAdmin(e.target.value === 'true')}
              className="w-full p-3 bg-[var(--background)] border border-[var(--border-color)] rounded-md focus:ring-[var(--accent)] focus:border-[var(--accent)]"
            >
              <option value="false">No (User)</option>
              <option value="true">Yes (Admin)</option>
            </select>
          </div>
          <div className="flex justify-end space-x-4 pt-2">
            <button
              type="button"
              onClick={onClose}
              className="py-2 px-4 border border-[var(--border-color)] rounded-md hover:bg-[var(--background)] transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="py-2 px-4 bg-[var(--accent)] text-[var(--background)] rounded-md hover:bg-cyan-500 transition-colors"
            >
              Add User
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default AddUserModal;
