// frontend/src/components/admin/EditUserModal.tsx
'use client';

import React, { useState, useEffect } from 'react';

// This interface should match EditableUserData from UserManagementTable
interface EditableUserFormData {
  id: string;
  email: string;
  username: string;
  isAdmin: boolean;
}

interface EditUserModalProps {
  isOpen: boolean;
  onClose: () => void;
  userToEdit: EditableUserFormData | null;
  onEditUser: (updatedUserData: EditableUserFormData) => void;
}

const EditUserModal: React.FC<EditUserModalProps> = ({ isOpen, onClose, userToEdit, onEditUser }) => {
  const [email, setEmail] = useState('');
  const [username, setUsername] = useState(''); // Added username state
  const [isAdmin, setIsAdmin] = useState(false); // Changed from role to isAdmin
  // Removed status state

  useEffect(() => {
    if (userToEdit) {
      setEmail(userToEdit.email);
      setUsername(userToEdit.username);
      setIsAdmin(userToEdit.isAdmin);
    } else {
      setEmail('');
      setUsername('');
      setIsAdmin(false);
    }
  }, [userToEdit, isOpen]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!userToEdit) return;
    if (!email || !username) { // Added username to validation
        alert('Email and Username are required.');
        return;
    }
    onEditUser({
      id: userToEdit.id, // Keep the original ID
      email,
      username,
      isAdmin
    });
    onClose();
  };

  if (!isOpen || !userToEdit) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-[var(--secondary-background)] p-8 rounded-lg shadow-xl w-full max-w-md text-[var(--foreground)]">
        <div className="flex justify-between items-center mb-6">
          <h2 className="text-2xl font-semibold text-[var(--accent)]">Edit User: {userToEdit.username || userToEdit.email}</h2>
          <button onClick={onClose} className="text-[var(--foreground)] hover:text-[var(--accent)] text-2xl">&times;</button>
        </div>
        <form onSubmit={handleSubmit} className="space-y-6">
          <div>
            <label htmlFor="edit-username" className="block text-sm font-medium mb-1">Username</label>
            <input
              type="text"
              id="edit-username"
              value={username}
              onChange={(e) => setUsername(e.target.value)}
              required
              className="w-full p-3 bg-[var(--background)] border border-[var(--border-color)] rounded-md focus:ring-[var(--accent)] focus:border-[var(--accent)]"
            />
          </div>
          <div>
            <label htmlFor="edit-email" className="block text-sm font-medium mb-1">Email Address</label>
            <input
              type="email"
              id="edit-email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className="w-full p-3 bg-[var(--background)] border border-[var(--border-color)] rounded-md focus:ring-[var(--accent)] focus:border-[var(--accent)]"
            />
          </div>

          <div>
            <label htmlFor="edit-isAdmin" className="block text-sm font-medium mb-1">Administrator</label>
            <select
              id="edit-isAdmin"
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
              Save Changes
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default EditUserModal;
