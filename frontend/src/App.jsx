import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import ChangePassword from "./pages/ChangePassword";
import LoanArchive from "./pages/LoanArchive";
import LoanDetail from "./pages/LoanDetail";
import LoanList from "./pages/LoanList";
import LoanNew from "./pages/LoanNew";
import LoanReturn from "./pages/LoanReturn";
import Storage from "./pages/Storage";

const queryClient = new QueryClient();
const scriptName = typeof window !== "undefined" ? window.SCRIPT_NAME || "" : "";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={scriptName}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<LoanList />} />
            <Route path="storage" element={<Storage />} />
            <Route path="loans" element={<LoanList />} />
            <Route path="loans/new" element={<LoanNew />} />
            <Route path="loans/archive" element={<LoanArchive />} />
            <Route path="loans/:id" element={<LoanDetail />} />
            <Route path="loans/:id/return" element={<LoanReturn />} />
            <Route path="account/password" element={<ChangePassword />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
