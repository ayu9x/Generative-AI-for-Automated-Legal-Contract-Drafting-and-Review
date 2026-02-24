import { Outlet, Link, useLocation } from 'react-router-dom';
import { useAuthStore } from '../store/authStore';
import NotificationCenter from './NotificationCenter';
import {
  FileText,
  Shield,
  AlertTriangle,
  Home,
  Plus,
  LogOut,
  User,
  FolderOpen,
  ClipboardList,
  Settings,
  MessageSquare,
  GitBranch,
  PenTool,
  HardDrive,
  FileUp,
  Search,
  BarChart3,
  BookOpen,
} from 'lucide-react';

const navItems = [
  { path: '/', label: 'Dashboard', icon: Home },
  { path: '/generate', label: 'Generate Contract', icon: Plus },
  { path: '/templates', label: 'Templates', icon: FolderOpen },
  { path: '/workflows', label: 'Workflows', icon: GitBranch },
  { path: '/sign', label: 'E-Signature', icon: PenTool },
  { path: '/collaboration', label: 'Collaboration', icon: MessageSquare },
  { path: '/drive', label: 'Document Drive', icon: HardDrive },
  { path: '/upload-analysis', label: 'Upload & Analyze', icon: FileUp },
  { path: '/risk-analysis', label: 'Risk Analysis', icon: AlertTriangle },
  { path: '/compliance', label: 'Compliance', icon: Shield },
  { path: '/search', label: 'Smart Search', icon: Search },
  { path: '/insights', label: 'Contract Insights', icon: BarChart3 },
  { path: '/knowledge', label: 'Knowledge Base', icon: BookOpen },
];

const adminNav = [
  { path: '/audit-logs', label: 'Audit Logs', icon: ClipboardList },
];

export default function Layout() {
  const { user, logout } = useAuthStore();
  const location = useLocation();

  const isAdmin = user?.role === 'ADMIN' || user?.role === 'LEGAL_ADMIN';

  return (
    <div className="flex h-screen bg-gray-50">
      {/* Sidebar */}
      <aside className="w-64 bg-legal-dark text-white flex flex-col shrink-0">
        <div className="p-6 border-b border-gray-700">
          <h1 className="text-xl font-bold flex items-center gap-2">
            <FileText className="w-6 h-6 text-primary-400" />
            Legal AI
          </h1>
          <p className="text-xs text-gray-400 mt-1">Contract Intelligence</p>
        </div>

        <nav className="flex-1 p-4 space-y-1 overflow-y-auto custom-scrollbar">
          {/* Main nav */}
          {navItems.map(({ path, label, icon: Icon }) => {
            const active = location.pathname === path;
            return (
              <Link
                key={path}
                to={path}
                className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${active
                  ? 'bg-primary-600 text-white'
                  : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                  }`}
              >
                <Icon className="w-5 h-5" />
                {label}
              </Link>
            );
          })}

          {/* Admin section */}
          {isAdmin && (
            <>
              <div className="pt-4 pb-2">
                <p className="px-4 text-xs font-semibold text-gray-500 uppercase tracking-wider">
                  Admin
                </p>
              </div>
              {adminNav.map(({ path, label, icon: Icon }) => {
                const active = location.pathname === path;
                return (
                  <Link
                    key={path}
                    to={path}
                    className={`flex items-center gap-3 px-4 py-3 rounded-lg text-sm transition-colors ${active
                      ? 'bg-primary-600 text-white'
                      : 'text-gray-300 hover:bg-gray-800 hover:text-white'
                      }`}
                  >
                    <Icon className="w-5 h-5" />
                    {label}
                  </Link>
                );
              })}
            </>
          )}
        </nav>

        {/* User section */}
        <div className="p-4 border-t border-gray-700">
          <div className="flex items-center gap-3 mb-3">
            <div className="w-8 h-8 bg-primary-600 rounded-full flex items-center justify-center">
              <User className="w-4 h-4" />
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">{user?.full_name}</p>
              <p className="text-xs text-gray-400 truncate">{user?.role}</p>
            </div>
          </div>
          <div className="space-y-1">
            <Link
              to="/settings"
              className={`flex items-center gap-2 px-4 py-2 w-full text-sm rounded-lg transition-colors ${location.pathname === '/settings'
                ? 'bg-primary-600 text-white'
                : 'text-gray-300 hover:text-white hover:bg-gray-800'
                }`}
            >
              <Settings className="w-4 h-4" />
              Settings
            </Link>
            <button
              onClick={logout}
              className="flex items-center gap-2 px-4 py-2 w-full text-sm text-gray-300 hover:text-white hover:bg-gray-800 rounded-lg transition-colors"
            >
              <LogOut className="w-4 h-4" />
              Sign Out
            </button>
          </div>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="flex-1 flex flex-col min-w-0 overflow-hidden">
        {/* Header */}
        <header className="h-16 bg-white border-b border-gray-200 flex items-center justify-between px-6 shrink-0 z-20 shadow-sm relative">
          <div className="flex items-center gap-4">
            {/* Breadcrumb or Page Title could go here */}
            <h2 className="font-semibold text-gray-800">
              {navItems.find(i => i.path === location.pathname)?.label ||
                adminNav.find(i => i.path === location.pathname)?.label ||
                (location.pathname === '/settings' ? 'Settings' : '')}
            </h2>
          </div>
          <div className="flex items-center gap-4">
            <NotificationCenter />
          </div>
        </header>

        {/* Page Content */}
        <main className="flex-1 overflow-auto bg-gray-50/50">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
