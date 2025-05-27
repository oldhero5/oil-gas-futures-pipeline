// frontend/src/components/admin/DeleteUserConfirmationModal.tsx
'use client';

import React from 'react';

interface UserData {
  id: string;
  email: string;
}

interface DeleteUserConfirmationModalProps {
  isOpen: boolean;
  onClose: () => void;
  userToDelete: UserData | null;
  onConfirmDelete: (userId: string) => void;
}

const DeleteUserConfirmationModal: React.FC<DeleteUserConfirmationModalProps> = ({ isOpen, onClose, userToDelete, onConfirmDelete }) => {
  if (!isOpen || !userToDelete) return null;

  const handleConfirm = () => {
    onConfirmDelete(userToDelete.id);
    onClose();
  };

  return (
    <div className="fixed inset-0 bg-black bg-opacity-75 flex items-center justify-center z-50 p-4">
      <div className="bg-[var(--secondary-background)] p-8 rounded-lg shadow-xl w-full max-w-md text-[var(--foreground)]">
        <div className="flex justify-between items-center mb-4">
          <h2 className="text-xl font-semibold text-[var(--accent)]">Confirm Deletion</h2>
          <button onClick={onClose} className="text-[var(--foreground)] hover:text-[var(--accent)] text-2xl">&times;</button>
        </div>
        <p className="mb-6">
          Are you sure you want to delete the user <strong className="text-[var(--accent)]">{userToDelete.email}</strong>?
          This action cannot be undone.
        </p>
        <div className="flex justify-end space-x-4">
          <button
            type="button"
            onClick={onClose}
            className="py-2 px-4 border border-[var(--border-color)] rounded-md hover:bg-[var(--background)] transition-colors"
          >
            Cancel
          </button>
          <button
            type="button"
            onClick={handleConfirm}
            className="py-2 px-4 bg-red-600 text-white rounded-md hover:bg-red-700 transition-colors"
          >
            Delete User
          </button>
        </div>
      </div>
    </div>
  );
};

export default DeleteUserConfirmationModal;
