import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { HelmetProvider } from "react-helmet-async";
import Index from "./pages/Index";
import HowItWorks from "./pages/HowItWorks";
import Match from "./pages/Match";
import DealMemos from "./pages/DealMemos";
import LaunchList from "./pages/LaunchList";
import About from "./pages/About";
import Contact from "./pages/Contact";
import Compliance from "./pages/Compliance";
import Investments from "./pages/Investments";
import InvestmentDetail from "./pages/InvestmentDetail";
import Guides from "./pages/Guides";
import GuideDetail from "./pages/GuideDetail";
import Answers from "./pages/Answers";
import AnswerDetail from "./pages/AnswerDetail";
import Team from "./pages/Team";
import Press from "./pages/Press";
import ClientStories from "./pages/ClientStories";
import Privacy from "./pages/Privacy";
import Terms from "./pages/Terms";
import Disclaimer from "./pages/Disclaimer";
import LandingInvestors from "./pages/LandingInvestors";
import LandingFirstTime from "./pages/LandingFirstTime";
import LandingExpats from "./pages/LandingExpats";
import AdminAuth from "./pages/AdminAuth";
import AdminDashboard from "./pages/AdminDashboard";
import AdminCollection from "./pages/AdminCollection";
import AdminUsers from "./pages/AdminUsers";
import AdminMarketing from "./pages/AdminMarketing";
import AdminChat from "./pages/AdminChat";
import AdminReset from "./pages/AdminReset";
import Qualification from "./pages/Qualification";
import NotFound from "./pages/NotFound";

const queryClient = new QueryClient();

const App = () => (
  <HelmetProvider>
    <QueryClientProvider client={queryClient}>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            <Route path="/" element={<Index />} />
            <Route path="/how-it-works" element={<HowItWorks />} />
            <Route path="/match" element={<Match />} />
            <Route path="/deal-memos" element={<DealMemos />} />
            <Route path="/launch-list" element={<LaunchList />} />
            <Route path="/about" element={<About />} />
            <Route path="/contact" element={<Contact />} />
            <Route path="/compliance" element={<Compliance />} />
            <Route path="/investments" element={<Investments />} />
            <Route path="/investments/:id" element={<InvestmentDetail />} />
            <Route path="/guides" element={<Guides />} />
            <Route path="/guides/:slug" element={<GuideDetail />} />
            <Route path="/answers" element={<Answers />} />
            <Route path="/answers/:slug" element={<AnswerDetail />} />
            <Route path="/team" element={<Team />} />
            <Route path="/press" element={<Press />} />
            <Route path="/client-stories" element={<ClientStories />} />
            <Route path="/privacy" element={<Privacy />} />
            <Route path="/terms" element={<Terms />} />
            <Route path="/disclaimer" element={<Disclaimer />} />
            <Route path="/lp/investors" element={<LandingInvestors />} />
            <Route path="/lp/first-time" element={<LandingFirstTime />} />
            <Route path="/lp/expats" element={<LandingExpats />} />
            <Route path="/qualification" element={<Qualification />} />
            <Route path="/admin" element={<AdminDashboard />} />
            <Route path="/admin/collection" element={<AdminCollection />} />
            <Route path="/admin/marketing" element={<AdminMarketing />} />
            <Route path="/admin/chat" element={<AdminChat />} />
            <Route path="/admin/users" element={<AdminUsers />} />
            <Route path="/admin/auth" element={<AdminAuth />} />
            <Route path="/admin/reset" element={<AdminReset />} />
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </QueryClientProvider>
  </HelmetProvider>
);

export default App;
