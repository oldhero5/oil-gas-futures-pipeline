// frontend/src/components/admin/UserManagementTable.tsx
'use client';

import React, { useState, useEffect } from 'react';
import AddUserModal from './AddUserModal';
import EditUserModal from './EditUserModal';
import DeleteUserConfirmationModal from './DeleteUserConfirmationModal';

interface User {
  id: string;
  email: string;
  username: string;
  isAdmin: boolean;
}

interface EditableUserData {
    id: string;
    email: string;
    username: string;
    isAdmin: boolean;
}

interface DeletableUserData {
    id: string;
    email: string;
}

const UserManagementTable: React.FC = () => {
  const [users, setUsers] = useState<User[]>([]);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [userToEdit, setUserToEdit] = useState<EditableUserData | null>(null);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [userToDelete, setUserToDelete] = useState<DeletableUserData | null>(null);

  useEffect(() => {
    const fetchUsers = async () => {
      setIsLoading(true);
      setError(null);
      try {
        const response = await fetch('/api/v1/users');
        if (!response.ok) {
          const errorData = await response.json().catch(() => ({ detail: 'Failed to parse error response' }));
          throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.detail || 'Unknown error'}`);
        }
        const data = await response.json();
        setUsers(data as User[]);
      } catch (e) {
        if (e instanceof Error) {
            setError(e.message);
        } else {
            setError('An unknown error occurred');
        }
        console.error("Failed to fetch users:", e);
      }
      setIsLoading(false);
    };

    fetchUsers();
  }, []);

  const refreshUsers = async () => {
    setIsLoading(true);
    setError(null);
    try {
      const response = await fetch('/api/v1/users');
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to parse error response' }));
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.detail || 'Unknown error'}`);
      }
      const data = await response.json();
      setUsers(data as User[]);
    } catch (e) {
      if (e instanceof Error) {
        setError(e.message);
      } else {
        setError('An unknown error occurred while refreshing users');
      }
      console.error("Failed to refresh users:", e);
    }
    setIsLoading(false);
  };

  const handleAction = (userId: string, action: string) => {
    const user = users.find(u => u.id === userId);
    if (!user) return;

    if (action === 'Edit') {
        setUserToEdit({ id: user.id, email: user.email, username: user.username, isAdmin: user.isAdmin });
        setIsEditModalOpen(true);
    } else if (action === 'Delete') {
        setUserToDelete({ id: user.id, email: user.email });
        setIsDeleteModalOpen(true);
    } else {
        alert(`Action: ${action} on User ID: ${userId} (Not implemented yet)`);
    }
  };

  const handleOpenAddModal = () => setIsAddModalOpen(true);
  const handleCloseAddModal = () => setIsAddModalOpen(false);

  const handleCloseEditModal = () => {
    setIsEditModalOpen(false);
    setUserToEdit(null);
  };

  const handleCloseDeleteModal = () => {
    setIsDeleteModalOpen(false);
    setUserToDelete(null);
  };

  const handleAddUser = async (newUserData: { email: string; username: string; password: string; isAdmin: boolean; }) => {
    setIsLoading(true);
    try {
      const response = await fetch('/api/v1/users', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(newUserData),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to parse error response' }));
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.detail || 'Failed to add user'}`);
      }
      alert(`User ${newUserData.email} added successfully!`);
      refreshUsers(); // Re-fetch users to update the table
    } catch (e) {
      let errorMessage = 'Failed to add user.';
      if (e instanceof Error) {
        errorMessage = e.message;
      }
      console.error("Add user error:", e);
      alert(`Error: ${errorMessage}`);
      setIsLoading(false); // Stop loading on error so user can try again
    }
    // setLoading(false) will be called by refreshUsers on success
  };

  const handleEditUser = async (updatedUserData: EditableUserData) => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/users/${updatedUserData.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        // Backend expects: email, username, password (optional), isAdmin
        // We are not sending password here, as it's usually a separate flow.
        body: JSON.stringify({
            email: updatedUserData.email,
            username: updatedUserData.username,
            isAdmin: updatedUserData.isAdmin,
            // password: can be added here if needed for edit, but typically not.
        }),
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to parse error response' }));
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.detail || 'Failed to update user'}`);
      }
      alert(`User ${updatedUserData.email} updated successfully!`);
      refreshUsers(); // Re-fetch users
    } catch (e) {
      let errorMessage = 'Failed to update user.';
      if (e instanceof Error) {
        errorMessage = e.message;
      }
      console.error("Edit user error:", e);
      alert(`Error: ${errorMessage}`);
      setIsLoading(false);
    }
  };

  const handleConfirmDeleteUser = async (userId: string) => {
    setIsLoading(true);
    try {
      const response = await fetch(`/api/v1/users/${userId}`, {
        method: 'DELETE',
      });
      if (!response.ok) {
        const errorData = await response.json().catch(() => ({ detail: 'Failed to parse error response' }));
        throw new Error(`HTTP error! status: ${response.status}, message: ${errorData.detail || 'Failed to delete user'}`);
      }
      alert(`User with ID: ${userId} deleted successfully!`);
      refreshUsers(); // Re-fetch users
    } catch (e) {
      let errorMessage = 'Failed to delete user.';
      if (e instanceof Error) {
        errorMessage = e.message;
      }
      console.error("Delete user error:", e);
      alert(`Error: ${errorMessage}`);
      setIsLoading(false);
    }
  };

  if (isLoading) return <div className="text-[var(--foreground)] p-6">Loading users...</div>;
  if (error) return <div className="text-red-500 p-6">Error loading users: {error}</div>;

  return (
    <div className="bg-[var(--secondary-background)] p-6 rounded-lg shadow-xl text-[var(--foreground)]">
      <div className="flex justify-between items-center mb-6">
        <h2 className="text-2xl font-semibold text-[var(--accent)]">User Management</h2>
        <button
          onClick={handleOpenAddModal}
          className="bg-[var(--accent)] hover:bg-cyan-500 text-[var(--background)] py-2 px-4 rounded-md text-sm transition-colors"
        >
          Add New User
        </button>
      </div>
      <div className="overflow-x-auto">
        <table className="min-w-full divide-y divide-[var(--border-color)]">
          <thead className="bg-[var(--background)]">
            <tr>
              {['Username', 'Email', 'Admin', 'Actions'].map((header) => (
                <th key={header} scope="col" className="px-6 py-3 text-left text-xs font-medium uppercase tracking-wider">
                  {header}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="divide-y divide-[var(--border-color)]">
            {users.map((user) => (
              <tr key={user.id} className="hover:bg-[var(--background)] transition-colors">
                <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-[var(--accent)]">{user.username}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{user.email}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm">{user.isAdmin ? 'Yes' : 'No'}</td>
                <td className="px-6 py-4 whitespace-nowrap text-sm space-x-2">
                  <button
                    onClick={() => handleAction(user.id, 'Edit')}
                    className="text-blue-400 hover:text-blue-300"
                  >
                    Edit
                  </button>
                  <button
                    onClick={() => handleAction(user.id, 'Delete')}
                    className="text-red-400 hover:text-red-300"
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <AddUserModal
        isOpen={isAddModalOpen}
        onClose={handleCloseAddModal}
        onAddUser={handleAddUser}
      />
      <EditUserModal
        isOpen={isEditModalOpen}
        onClose={handleCloseEditModal}
        userToEdit={userToEdit}
        onEditUser={handleEditUser}
      />
      <DeleteUserConfirmationModal
        isOpen={isDeleteModalOpen}
        onClose={handleCloseDeleteModal}
        userToDelete={userToDelete}
        onConfirmDelete={handleConfirmDeleteUser}
      />
    </div>
  );
};

export default UserManagementTable;
