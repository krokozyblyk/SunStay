import { lazy, Suspense } from "react";
import { Navigate, Route, Routes } from "react-router-dom";
import { AppShell, PublicLayout, RequireAuth, RequireRole } from "./components/Layout";
import { PageSkeleton } from "./components/PageState";
import { LandingPage, SearchPage, CheckoutPage, ConfirmationPage, LoginPage } from "./pages/PublicPages";
import {
  GuestBookingDetailPage,
  GuestBookingsPage,
  GuestDashboardPage,
  GuestInvoicesPage,
  GuestLoyaltyPage,
  GuestProfilePage,
  GuestServicesPage,
} from "./pages/GuestPages";
import {
  BookingDetailPage,
  BookingsRegistryPage,
  FolioPaymentsPage,
  ManagerDashboardPage,
  RoomGridPage,
  FloorPlanPage,
  WaitlistPage,
} from "./pages/ManagerPages";
const ReportsPage = lazy(() => import("./pages/ReportsPage").then((module) => ({ default: module.ReportsPage })));
const HousekeepingBoardPage = lazy(() => import("./pages/OperationsPages").then((module) => ({ default: module.HousekeepingBoardPage })));
const MaintenancePage = lazy(() => import("./pages/OperationsPages").then((module) => ({ default: module.MaintenancePage })));
const ConsumablesPage = lazy(() => import("./pages/OperationsPages").then((module) => ({ default: module.ConsumablesPage })));
const AdminAuditPage = lazy(() => import("./pages/AdminPages").then((module) => ({ default: module.AdminAuditPage })));
const AdminBackupsPage = lazy(() => import("./pages/AdminPages").then((module) => ({ default: module.AdminBackupsPage })));
const AdminDirectoriesPage = lazy(() => import("./pages/AdminPages").then((module) => ({ default: module.AdminDirectoriesPage })));
const AdminReviewsPage = lazy(() => import("./pages/AdminPages").then((module) => ({ default: module.AdminReviewsPage })));
const AdminSessionsPage = lazy(() => import("./pages/AdminPages").then((module) => ({ default: module.AdminSessionsPage })));
const AdminSettingsPage = lazy(() => import("./pages/AdminPages").then((module) => ({ default: module.AdminSettingsPage })));
const AdminUsersPage = lazy(() => import("./pages/AdminPages").then((module) => ({ default: module.AdminUsersPage })));
const EmployeesPage = lazy(() => import("./pages/AdminPages").then((module) => ({ default: module.EmployeesPage })));

const STAFF = ["MANAGER", "HOUSEKEEPING", "HOTEL_MANAGER", "DB_ADMIN"];
const MANAGERS = ["MANAGER", "HOTEL_MANAGER", "DB_ADMIN"];

export default function App() {
  return (
    <Suspense fallback={<PageSkeleton />}>
    <Routes>
      <Route element={<PublicLayout />}>
        <Route path="/" element={<LandingPage />} />
        <Route path="/search" element={<SearchPage />} />
        <Route path="/checkout" element={<CheckoutPage />} />
        <Route path="/confirmation" element={<ConfirmationPage />} />
      </Route>

      <Route path="/login" element={<LoginPage />} />

      <Route
        element={
          <RequireAuth>
            <RequireRole roles={STAFF}>
              <AppShell />
            </RequireRole>
          </RequireAuth>
        }
      >
        <Route path="/app" element={<RequireRole roles={MANAGERS}><ManagerDashboardPage /></RequireRole>} />
        <Route path="/app/room-grid" element={<RequireRole roles={MANAGERS}><RoomGridPage /></RequireRole>} />
        <Route path="/app/waitlist" element={<RequireRole roles={MANAGERS}><WaitlistPage /></RequireRole>} />
        <Route path="/app/floor-plan" element={<RequireRole roles={MANAGERS}><FloorPlanPage /></RequireRole>} />
        <Route path="/app/bookings" element={<RequireRole roles={MANAGERS}><BookingsRegistryPage /></RequireRole>} />
        <Route path="/app/bookings/:id" element={<RequireRole roles={MANAGERS}><BookingDetailPage /></RequireRole>} />
        <Route path="/app/folios" element={<RequireRole roles={MANAGERS}><FolioPaymentsPage /></RequireRole>} />
        <Route path="/app/reports" element={<RequireRole roles={MANAGERS}><ReportsPage /></RequireRole>} />
        <Route path="/app/housekeeping" element={<RequireRole roles={STAFF}><HousekeepingBoardPage /></RequireRole>} />
        <Route path="/app/maintenance" element={<RequireRole roles={STAFF}><MaintenancePage /></RequireRole>} />
        <Route path="/app/consumables" element={<RequireRole roles={["HOUSEKEEPING", "DB_ADMIN", "HOTEL_MANAGER"]}><ConsumablesPage /></RequireRole>} />
        <Route path="/app/admin/users" element={<RequireRole roles={["DB_ADMIN"]}><AdminUsersPage /></RequireRole>} />
        <Route path="/app/employees" element={<RequireRole roles={["HOTEL_MANAGER", "DB_ADMIN"]}><EmployeesPage /></RequireRole>} />
        <Route path="/app/admin/directories" element={<RequireRole roles={["HOTEL_MANAGER", "DB_ADMIN"]}><AdminDirectoriesPage /></RequireRole>} />
        <Route path="/app/admin/audit" element={<RequireRole roles={["HOTEL_MANAGER", "DB_ADMIN"]}><AdminAuditPage /></RequireRole>} />
        <Route path="/app/admin/reviews" element={<RequireRole roles={["HOTEL_MANAGER", "DB_ADMIN"]}><AdminReviewsPage /></RequireRole>} />
        <Route path="/app/admin/backups" element={<RequireRole roles={["DB_ADMIN"]}><AdminBackupsPage /></RequireRole>} />
        <Route path="/app/admin/sessions" element={<RequireRole roles={["DB_ADMIN"]}><AdminSessionsPage /></RequireRole>} />
        <Route path="/app/admin/settings" element={<RequireRole roles={["DB_ADMIN"]}><AdminSettingsPage /></RequireRole>} />
      </Route>

      <Route
        path="/me"
        element={
          <RequireAuth>
            <RequireRole roles={["GUEST"]}>
              <AppShell />
            </RequireRole>
          </RequireAuth>
        }
      >
        <Route index element={<GuestDashboardPage />} />
        <Route path="bookings" element={<GuestBookingsPage />} />
        <Route path="bookings/:id" element={<GuestBookingDetailPage />} />
        <Route path="invoices" element={<GuestInvoicesPage />} />
        <Route path="services" element={<GuestServicesPage />} />
        <Route path="profile" element={<GuestProfilePage />} />
        <Route path="loyalty" element={<GuestLoyaltyPage />} />
      </Route>

      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
    </Suspense>
  );
}
