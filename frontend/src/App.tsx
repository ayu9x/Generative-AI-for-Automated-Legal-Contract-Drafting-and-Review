import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuthStore } from './store/authStore';
import Layout from './components/Layout';
import Login from './pages/Login';
import Dashboard from './pages/Dashboard';
import ContractGenerator from './pages/ContractGenerator';
import ContractView from './pages/ContractView';
import RiskAnalysis from './pages/RiskAnalysis';
import ComplianceCenter from './pages/ComplianceCenter';
import VersionHistory from './pages/VersionHistory';
import TemplateLibrary from './pages/TemplateLibrary';
import ClauseLibrary from './pages/ClauseLibrary';
import AuditLogs from './pages/AuditLogs';
import Settings from './pages/Settings';

function ProtectedRoute({ children }: { children: React.ReactNode }) {
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated);
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
}

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route
        path="/"
        element={
          <ProtectedRoute>
            <Layout />
          </ProtectedRoute>
        }
      >
        <Route index element={<Dashboard />} />
        <Route path="generate" element={<ContractGenerator />} />
        <Route path="contracts/:id" element={<ContractView />} />
        <Route path="risk-analysis" element={<RiskAnalysis />} />
        <Route path="compliance" element={<ComplianceCenter />} />
        <Route path="versions/:contractId" element={<VersionHistory />} />
        <Route path="templates" element={<TemplateLibrary />} />
        <Route path="clauses" element={<ClauseLibrary />} />
        <Route path="audit-logs" element={<AuditLogs />} />
        <Route path="settings" element={<Settings />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
