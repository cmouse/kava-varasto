import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import Home from "./pages/Home";

const queryClient = new QueryClient();
const scriptName = typeof window !== "undefined" ? window.SCRIPT_NAME || "" : "";

function App() {
  return (
    <QueryClientProvider client={queryClient}>
      <BrowserRouter basename={scriptName}>
        <Routes>
          <Route element={<Layout />}>
            <Route index element={<Home />} />
          </Route>
        </Routes>
      </BrowserRouter>
    </QueryClientProvider>
  );
}

export default App;
