import { Routes, Route } from "react-router-dom";
import Layout from "./components/layout/Layout";
import OverviewPage from "./pages/OverviewPage";
import EndpointsPage from "./pages/EndpointsPage";
import EndpointDetailPage from "./pages/EndpointDetailPage";
import SoftwarePage from "./pages/SoftwarePage";
import SoftwareEndpointsPage from "./pages/SoftwareEndpointsPage";
import SoftwareVersionsPage from "./pages/SoftwareVersionsPage";
import SoftwareCompliancePage from "./pages/SoftwareCompliancePage";
import SoftwareSettingsPage from "./pages/SoftwareSettingsPage";
import WindowsUpdatesPage from "./pages/WindowsUpdatesPage";
import PatchCatalogPage from "./pages/PatchCatalogPage";
import SyncJobsPage from "./pages/SyncJobsPage";
import SettingsPage from "./pages/SettingsPage";

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route path="/" element={<OverviewPage />} />
        <Route path="/endpoints" element={<EndpointsPage />} />
        <Route path="/endpoints/:id" element={<EndpointDetailPage />} />
        <Route path="/software" element={<SoftwarePage />} />
        <Route path="/software/endpoints" element={<SoftwareEndpointsPage />} />
        <Route path="/software/versions" element={<SoftwareVersionsPage />} />
        <Route path="/software-compliance" element={<SoftwareCompliancePage />} />
        <Route path="/software-settings" element={<SoftwareSettingsPage />} />
        <Route path="/updates" element={<WindowsUpdatesPage />} />
        <Route path="/patch-catalog" element={<PatchCatalogPage />} />
        <Route path="/sync" element={<SyncJobsPage />} />
        <Route path="/settings" element={<SettingsPage />} />
      </Route>
    </Routes>
  );
}
