import { Navigate, Route, Routes } from "react-router-dom";
import { HomePage } from "../pages/HomePage";
import { ScriptStudioPage } from "../pages/ScriptStudioPage";
import { IdeaDetailPage } from "../pages/IdeaDetailPage";

export function AppRoutes() {
  return (
    <Routes>
      <Route path="/" element={<HomePage />} />
      <Route path="/script-studio" element={<ScriptStudioPage />} />
      <Route path="/ideas/:ideaId" element={<IdeaDetailPage />} />
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
