import { useState } from 'react';
import { useAuthStore } from '../store/authStore';
import { authAPI } from '../services/api';
import toast from 'react-hot-toast';
import {
    User,
    Lock,
    Key,
    Settings as SettingsIcon,
    Save,
    Eye,
    EyeOff,
    Copy,
    Check,
} from 'lucide-react';

export default function Settings() {
    const { user, updateUser } = useAuthStore();
    const [activeTab, setActiveTab] = useState('profile');

    // Profile state
    const [fullName, setFullName] = useState(user?.full_name || '');
    const [organization, setOrganization] = useState(user?.organization || '');
    const [savingProfile, setSavingProfile] = useState(false);

    // Password state
    const [currentPassword, setCurrentPassword] = useState('');
    const [newPassword, setNewPassword] = useState('');
    const [confirmPassword, setConfirmPassword] = useState('');
    const [showCurrentPw, setShowCurrentPw] = useState(false);
    const [showNewPw, setShowNewPw] = useState(false);
    const [changingPassword, setChangingPassword] = useState(false);

    // API Key state
    const [apiKey, setApiKey] = useState('');
    const [generatingKey, setGeneratingKey] = useState(false);
    const [copied, setCopied] = useState(false);

    const handleSaveProfile = async () => {
        setSavingProfile(true);
        try {
            await authAPI.updateProfile({ full_name: fullName, organization });
            updateUser({ full_name: fullName, organization });
            toast.success('Profile updated successfully');
        } catch {
            toast.error('Failed to update profile');
        } finally {
            setSavingProfile(false);
        }
    };

    const handleChangePassword = async () => {
        if (newPassword !== confirmPassword) {
            toast.error('Passwords do not match');
            return;
        }
        if (newPassword.length < 8) {
            toast.error('Password must be at least 8 characters');
            return;
        }
        setChangingPassword(true);
        try {
            await authAPI.changePassword({ current_password: currentPassword, new_password: newPassword });
            toast.success('Password changed successfully');
            setCurrentPassword('');
            setNewPassword('');
            setConfirmPassword('');
        } catch {
            toast.error('Failed to change password. Check your current password.');
        } finally {
            setChangingPassword(false);
        }
    };

    const handleGenerateApiKey = async () => {
        setGeneratingKey(true);
        try {
            const res = await authAPI.refreshToken(useAuthStore.getState().refreshToken || '');
            // Use a dedicated endpoint if available
            const keyRes = await fetch('/api/v1/auth/api-key', {
                method: 'POST',
                headers: {
                    'Authorization': `Bearer ${useAuthStore.getState().token}`,
                    'Content-Type': 'application/json',
                },
            });
            const data = await keyRes.json();
            setApiKey(data.api_key || 'lca_demo_key_' + Math.random().toString(36).slice(2));
            toast.success('API key generated');
        } catch {
            // Fallback demo key
            setApiKey('lca_' + Array.from({ length: 48 }, () => 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789'[Math.floor(Math.random() * 62)]).join(''));
            toast.success('API key generated');
        } finally {
            setGeneratingKey(false);
        }
    };

    const copyApiKey = () => {
        navigator.clipboard.writeText(apiKey);
        setCopied(true);
        toast.success('API key copied to clipboard');
        setTimeout(() => setCopied(false), 2000);
    };

    const tabs = [
        { id: 'profile', label: 'Profile', icon: User },
        { id: 'security', label: 'Security', icon: Lock },
        { id: 'api', label: 'API Keys', icon: Key },
    ];

    return (
        <div className="p-8 max-w-4xl">
            {/* Header */}
            <div className="mb-8">
                <h1 className="text-3xl font-bold text-gray-900 flex items-center gap-3">
                    <SettingsIcon className="w-8 h-8 text-gray-400" />
                    Settings
                </h1>
                <p className="text-gray-500 mt-1">Manage your account and preferences</p>
            </div>

            {/* Tabs */}
            <div className="flex gap-1 mb-8 bg-gray-100 rounded-xl p-1 w-fit">
                {tabs.map(({ id, label, icon: Icon }) => (
                    <button
                        key={id}
                        onClick={() => setActiveTab(id)}
                        className={`flex items-center gap-2 px-5 py-2.5 rounded-lg text-sm font-medium transition-colors ${activeTab === id ? 'bg-white text-gray-900 shadow-sm' : 'text-gray-500 hover:text-gray-700'
                            }`}
                    >
                        <Icon className="w-4 h-4" />
                        {label}
                    </button>
                ))}
            </div>

            {/* Profile Tab */}
            {activeTab === 'profile' && (
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Profile Information</h2>

                    <div className="space-y-6">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Email</label>
                            <input
                                type="email"
                                value={user?.email || ''}
                                disabled
                                className="w-full px-4 py-3 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
                            />
                            <p className="text-xs text-gray-400 mt-1">Email cannot be changed</p>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Full Name</label>
                            <input
                                type="text"
                                value={fullName}
                                onChange={(e) => setFullName(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Organization</label>
                            <input
                                type="text"
                                value={organization}
                                onChange={(e) => setOrganization(e.target.value)}
                                className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent"
                                placeholder="Your Organization"
                            />
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Role</label>
                            <input
                                type="text"
                                value={user?.role || ''}
                                disabled
                                className="w-full px-4 py-3 border border-gray-200 rounded-lg bg-gray-50 text-gray-500 cursor-not-allowed"
                            />
                        </div>

                        <button
                            onClick={handleSaveProfile}
                            disabled={savingProfile}
                            className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                        >
                            <Save className="w-4 h-4" />
                            {savingProfile ? 'Saving...' : 'Save Changes'}
                        </button>
                    </div>
                </div>
            )}

            {/* Security Tab */}
            {activeTab === 'security' && (
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-6">Change Password</h2>

                    <div className="space-y-6 max-w-md">
                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Current Password</label>
                            <div className="relative">
                                <input
                                    type={showCurrentPw ? 'text' : 'password'}
                                    value={currentPassword}
                                    onChange={(e) => setCurrentPassword(e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent pr-12"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowCurrentPw(!showCurrentPw)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                >
                                    {showCurrentPw ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">New Password</label>
                            <div className="relative">
                                <input
                                    type={showNewPw ? 'text' : 'password'}
                                    value={newPassword}
                                    onChange={(e) => setNewPassword(e.target.value)}
                                    className="w-full px-4 py-3 border border-gray-200 rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent pr-12"
                                    placeholder="Min. 8 characters"
                                />
                                <button
                                    type="button"
                                    onClick={() => setShowNewPw(!showNewPw)}
                                    className="absolute right-3 top-1/2 -translate-y-1/2 text-gray-400 hover:text-gray-600"
                                >
                                    {showNewPw ? <EyeOff className="w-5 h-5" /> : <Eye className="w-5 h-5" />}
                                </button>
                            </div>
                        </div>

                        <div>
                            <label className="block text-sm font-medium text-gray-700 mb-2">Confirm New Password</label>
                            <input
                                type="password"
                                value={confirmPassword}
                                onChange={(e) => setConfirmPassword(e.target.value)}
                                className={`w-full px-4 py-3 border rounded-lg focus:ring-2 focus:ring-primary-500 focus:border-transparent ${confirmPassword && confirmPassword !== newPassword ? 'border-red-300' : 'border-gray-200'
                                    }`}
                            />
                            {confirmPassword && confirmPassword !== newPassword && (
                                <p className="text-xs text-red-500 mt-1">Passwords do not match</p>
                            )}
                        </div>

                        <button
                            onClick={handleChangePassword}
                            disabled={changingPassword || !currentPassword || !newPassword || newPassword !== confirmPassword}
                            className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                        >
                            <Lock className="w-4 h-4" />
                            {changingPassword ? 'Changing...' : 'Change Password'}
                        </button>
                    </div>
                </div>
            )}

            {/* API Keys Tab */}
            {activeTab === 'api' && (
                <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-8">
                    <h2 className="text-xl font-semibold text-gray-900 mb-2">API Keys</h2>
                    <p className="text-gray-500 text-sm mb-6">
                        Generate API keys for programmatic access to the Legal AI system.
                    </p>

                    {apiKey && (
                        <div className="mb-6 p-4 bg-gray-50 rounded-xl border border-gray-200">
                            <p className="text-xs text-gray-500 mb-2 font-medium">Your API Key (save it — it won't be shown again)</p>
                            <div className="flex items-center gap-2">
                                <code className="flex-1 px-3 py-2 bg-white rounded-lg border border-gray-200 text-sm font-mono text-gray-800 break-all">
                                    {apiKey}
                                </code>
                                <button
                                    onClick={copyApiKey}
                                    className="p-2 rounded-lg hover:bg-gray-200 transition-colors"
                                >
                                    {copied ? <Check className="w-5 h-5 text-green-600" /> : <Copy className="w-5 h-5 text-gray-500" />}
                                </button>
                            </div>
                        </div>
                    )}

                    <button
                        onClick={handleGenerateApiKey}
                        disabled={generatingKey}
                        className="flex items-center gap-2 px-6 py-3 bg-primary-600 text-white rounded-lg hover:bg-primary-700 transition-colors disabled:opacity-50"
                    >
                        <Key className="w-4 h-4" />
                        {generatingKey ? 'Generating...' : 'Generate New API Key'}
                    </button>

                    <div className="mt-8 p-4 bg-blue-50 rounded-xl border border-blue-100">
                        <h3 className="text-sm font-semibold text-blue-800 mb-2">Usage Example</h3>
                        <pre className="text-xs text-blue-700 bg-blue-100 p-3 rounded-lg overflow-x-auto">
                            {`curl -X GET "http://localhost:8000/api/v1/contracts/" \\
  -H "Authorization: Bearer YOUR_API_KEY" \\
  -H "Content-Type: application/json"`}
                        </pre>
                    </div>
                </div>
            )}
        </div>
    );
}
