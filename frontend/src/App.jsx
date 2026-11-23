import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './layouts/Layout';
import ErrorBoundary from './components/ErrorBoundary';
import Overview from './pages/Overview';
import Inspections from './pages/Inspections';
import DefectPrediction from './pages/DefectPrediction';
import DefectAnalysis from './pages/DefectAnalysis';
import QualityAnalytics from './pages/QualityAnalytics';
import Reports from './pages/Reports';
import Settings from './pages/Settings';

export default function App() {
  return (
    <BrowserRouter>
      <ErrorBoundary>
        <Routes>
          <Route path="/" element={<Layout />}>
            <Route index element={<Overview />} />
            <Route path="inspections" element={<Inspections />} />
            <Route path="prediction" element={<DefectPrediction />} />
            <Route path="predict" element={<Navigate to="/prediction" replace />} />
            <Route path="analysis" element={<DefectAnalysis />} />
            <Route path="defects" element={<Navigate to="/analysis" replace />} />
            <Route path="analytics" element={<QualityAnalytics />} />
            <Route path="reports" element={<Reports />} />
            <Route path="settings" element={<Settings />} />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Route>
        </Routes>
      </ErrorBoundary>
    </BrowserRouter>
  );
}
