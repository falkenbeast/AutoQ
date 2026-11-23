/**
 * AutoQ - Automotive Quality Intelligence System
 * Domain-accurate demonstration dataset for Phase 2 UI presentation.
 * 
 * IMPORTANT: This data is explicitly flagged as DEMONSTRATION DATA for
 * pre-production UI prototyping prior to database ingestion (Phase 3).
 */

export const IS_DEMO_DATA = true;

// Key Performance Indicators (Demo Baseline)
export const OVERVIEW_KPIS = {
  totalInspections: {
    value: "1,482",
    rawValue: 1482,
    label: "Total Inspections",
    change: "+12.4%",
    isPositive: true,
    subtext: "vs previous 30 days",
  },
  passedComponents: {
    value: "1,348",
    rawValue: 1348,
    label: "Passed Components",
    change: "+9.1%",
    isPositive: true,
    subtext: "90.96% first-pass yield",
  },
  defectiveComponents: {
    value: "134",
    rawValue: 134,
    label: "Defective Components",
    change: "-3.3%",
    isPositive: true, // fewer defects is good
    subtext: "Flagged for rework / scrap",
  },
  defectRate: {
    value: "9.04%",
    rawValue: 9.04,
    label: "Overall Defect Rate",
    change: "-1.2%",
    isPositive: true,
    subtext: "Tolerance threshold: < 10.0%",
  },
  predictionAccuracy: {
    value: "94.2%",
    rawValue: 94.2,
    label: "ML Engine Target Accuracy",
    change: "Pending Training",
    isPositive: null,
    subtext: "Target baseline (Phase 3)",
  },
};

// Daily inspection trends (past 14 days)
export const DAILY_INSPECTION_TRENDS = [
  { date: "Nov 05", inspections: 98, passed: 91, defective: 7, defectRate: 7.1 },
  { date: "Nov 06", inspections: 104, passed: 96, defective: 8, defectRate: 7.7 },
  { date: "Nov 07", inspections: 112, passed: 101, defective: 11, defectRate: 9.8 },
  { date: "Nov 08", inspections: 95, passed: 87, defective: 8, defectRate: 8.4 },
  { date: "Nov 09", inspections: 118, passed: 104, defective: 14, defectRate: 11.9 },
  { date: "Nov 10", inspections: 106, passed: 97, defective: 9, defectRate: 8.5 },
  { date: "Nov 11", inspections: 115, passed: 103, defective: 12, defectRate: 10.4 },
  { date: "Nov 12", inspections: 122, passed: 112, defective: 10, defectRate: 8.2 },
  { date: "Nov 13", inspections: 108, passed: 99, defective: 9, defectRate: 8.3 },
  { date: "Nov 14", inspections: 116, passed: 105, defective: 11, defectRate: 9.5 },
  { date: "Nov 15", inspections: 125, passed: 115, defective: 10, defectRate: 8.0 },
  { date: "Nov 16", inspections: 92, passed: 85, defective: 7, defectRate: 7.6 },
  { date: "Nov 17", inspections: 110, passed: 102, defective: 8, defectRate: 7.3 },
  { date: "Nov 18", inspections: 128, passed: 118, defective: 10, defectRate: 7.8 },
];

// Defect Categories Distribution
export const DEFECT_CATEGORIES = [
  { name: "Structural Porosity", count: 48, percentage: 35.8, color: "#EF4444" },
  { name: "Dimensional Variance", count: 34, percentage: 25.4, color: "#F59E0B" },
  { name: "Surface Micro-cracks", count: 26, percentage: 19.4, color: "#3B82F6" },
  { name: "Thermal Distortion", count: 16, percentage: 11.9, color: "#06B6D4" },
  { name: "Threading / Machining Defect", count: 10, percentage: 7.5, color: "#8B5CF6" },
];

// Component Quality Performance
export const COMPONENT_QUALITY_PERFORMANCE = [
  { category: "Brake Caliper", passed: 310, defective: 28, passRate: 91.7 },
  { category: "Crankshaft", passed: 245, defective: 18, passRate: 93.1 },
  { category: "Turbo Housing", passed: 195, defective: 32, passRate: 85.9 },
  { category: "Gear Assembly", passed: 280, defective: 22, passRate: 92.7 },
  { category: "Steering Knuckle", passed: 180, defective: 21, passRate: 89.5 },
  { category: "Engine Cylinder Head", passed: 138, defective: 13, passRate: 91.4 },
];

// Production Batch Comparison
export const BATCH_COMPARISON_DATA = [
  { batch: "BATCH-2026-A1", total: 320, passed: 298, defective: 22, defectRate: 6.9, avgTemp: 742, avgPressure: 142 },
  { batch: "BATCH-2026-A2", total: 340, passed: 312, defective: 28, defectRate: 8.2, avgTemp: 755, avgPressure: 148 },
  { batch: "BATCH-2026-B1", total: 310, passed: 275, defective: 35, defectRate: 11.3, avgTemp: 782, avgPressure: 160 },
  { batch: "BATCH-2026-B2", total: 290, passed: 258, defective: 32, defectRate: 11.0, avgTemp: 778, avgPressure: 156 },
  { batch: "BATCH-2026-C1", total: 222, passed: 205, defective: 17, defectRate: 7.7, avgTemp: 738, avgPressure: 140 },
];

// Recent Inspections Detailed List
export const INITIAL_INSPECTIONS = [
  {
    id: "AQ-2026-0941",
    componentId: "CMP-BRK-401",
    componentName: "Ventilated Brake Caliper Mount",
    category: "Braking System",
    batch: "BATCH-2026-A2",
    date: "2026-11-18 14:32",
    temperature: 742,
    pressure: 145,
    status: "PASSED",
    defectCategory: "None",
    inspector: "QC-Lead-03",
    notes: "Dimensions within ±0.02mm tolerance limit.",
  },
  {
    id: "AQ-2026-0940",
    componentId: "CMP-TRB-809",
    componentName: "Variable Geometry Turbo Housing",
    category: "Powertrain",
    batch: "BATCH-2026-B1",
    date: "2026-11-18 13:45",
    temperature: 785,
    pressure: 164,
    status: "DEFECTIVE",
    defectCategory: "Structural Porosity",
    inspector: "QC-Lead-01",
    notes: "Ultrasonic density scan indicated sub-surface voids exceeding 0.4mm.",
  },
  {
    id: "AQ-2026-0939",
    componentId: "CMP-CRK-102",
    componentName: "Forged Alloy Crankshaft V6",
    category: "Engine",
    batch: "BATCH-2026-A1",
    date: "2026-11-18 12:15",
    temperature: 738,
    pressure: 142,
    status: "PASSED",
    defectCategory: "None",
    inspector: "QC-Lead-02",
    notes: "Dynamic balancing within ISO 1940 G2.5 spec.",
  },
  {
    id: "AQ-2026-0938",
    componentId: "CMP-STR-552",
    componentName: "Cast Aluminum Steering Knuckle",
    category: "Chassis & Steering",
    batch: "BATCH-2026-B2",
    date: "2026-11-18 11:20",
    temperature: 772,
    pressure: 158,
    status: "DEFECTIVE",
    defectCategory: "Surface Micro-cracks",
    inspector: "QC-Lead-03",
    notes: "Eddy-current probe revealed fatigue micro-fissures around pivot boss.",
  },
  {
    id: "AQ-2026-0937",
    componentId: "CMP-GER-310",
    componentName: "Helical Transmission Input Gear",
    category: "Transmission",
    batch: "BATCH-2026-A2",
    date: "2026-11-18 10:05",
    temperature: 746,
    pressure: 144,
    status: "PASSED",
    defectCategory: "None",
    inspector: "QC-Lead-02",
    notes: "Gear tooth flank hardness test passed (60 HRC).",
  },
  {
    id: "AQ-2026-0936",
    componentId: "CMP-ENG-612",
    componentName: "Dual Overhead Cam Cylinder Head",
    category: "Engine",
    batch: "BATCH-2026-B1",
    date: "2026-11-17 16:50",
    temperature: 789,
    pressure: 162,
    status: "DEFECTIVE",
    defectCategory: "Dimensional Variance",
    inspector: "QC-Lead-01",
    notes: "Combustion chamber deck flatness deviation of 0.08mm (limit 0.05mm).",
  },
  {
    id: "AQ-2026-0935",
    componentId: "CMP-BRK-408",
    componentName: "Rear Brake Disc Rotor Assembly",
    category: "Braking System",
    batch: "BATCH-2026-A1",
    date: "2026-11-17 15:10",
    temperature: 735,
    pressure: 140,
    status: "PASSED",
    defectCategory: "None",
    inspector: "QC-Lead-03",
    notes: "Rotor lateral runout within 0.03mm spec.",
  },
  {
    id: "AQ-2026-0934",
    componentId: "CMP-TRB-814",
    componentName: "Twin-Scroll Turbine Casing",
    category: "Powertrain",
    batch: "BATCH-2026-B2",
    date: "2026-11-17 14:02",
    temperature: 781,
    pressure: 159,
    status: "DEFECTIVE",
    defectCategory: "Thermal Distortion",
    inspector: "QC-Lead-02",
    notes: "Exhaust manifold mating flange warped due to thermal quenching cycle.",
  },
  {
    id: "AQ-2026-0933",
    componentId: "CMP-SUS-218",
    componentName: "Lower Control Wishbone Arm",
    category: "Chassis & Steering",
    batch: "BATCH-2026-C1",
    date: "2026-11-17 11:40",
    temperature: 739,
    pressure: 141,
    status: "PASSED",
    defectCategory: "None",
    inspector: "QC-Lead-01",
    notes: "Bushing bore press fit clearance nominal.",
  },
  {
    id: "AQ-2026-0932",
    componentId: "CMP-GER-319",
    componentName: "Synchronizer Sleeve Collar",
    category: "Transmission",
    batch: "BATCH-2026-B1",
    date: "2026-11-16 16:22",
    temperature: 768,
    pressure: 153,
    status: "DEFECTIVE",
    defectCategory: "Threading / Machining Defect",
    inspector: "QC-Lead-02",
    notes: "Spline teeth profile pitch error detected on optical comparator.",
  },
];

// Recurring Defect Patterns for Defect Analysis
export const RECURRING_DEFECT_PATTERNS = [
  {
    id: "PAT-01",
    title: "High-Temperature Thermal Porosity in Cast Turbine Casings",
    frequency: "High (35.8% of defects)",
    affectedCategory: "Powertrain / Casting",
    primaryFactor: "Manufacturing temperature > 775°C combined with injection pressure > 155 bar",
    severity: "High",
    recommendedInvestigation: "Recalibrate die cooling channels and review secondary alloy degassing logs.",
  },
  {
    id: "PAT-02",
    title: "Batch B Flange Flatness Variance",
    frequency: "Medium (25.4% of defects)",
    affectedCategory: "Engine & Cylinder Heads",
    primaryFactor: "Tooling wear after 4,000 cycles on CNC Milling Station 04",
    severity: "Medium",
    recommendedInvestigation: "Schedule carbide insert replacement and spindle runout alignment.",
  },
  {
    id: "PAT-03",
    title: "Surface Micro-fissures in Rapid Quenched Steering Knuckles",
    frequency: "Moderate (19.4% of defects)",
    affectedCategory: "Chassis & Steering",
    primaryFactor: "Excessive cooling gradient during quench chamber transfer",
    severity: "High",
    recommendedInvestigation: "Adjust quench water temperature from 22°C to 38°C to attenuate thermal shock.",
  },
];

// Historical Reports List (Phase 2 preview data)
export const REPORT_HISTORY = [
  {
    id: "REP-2026-1101",
    title: "Weekly Component Quality Audit - Batch 2026-B1/B2",
    type: "Defect Analysis",
    generatedDate: "2026-11-18 09:00",
    generatedBy: "Lead Quality Engineer",
    size: "2.4 MB",
    status: "Generated",
    format: "PDF",
  },
  {
    id: "REP-2026-1098",
    title: "Casting Porosity & Tolerance Evaluation Report",
    type: "Inspection Summary",
    generatedDate: "2026-11-15 17:30",
    generatedBy: "System Automation",
    size: "1.8 MB",
    status: "Generated",
    format: "PDF",
  },
  {
    id: "REP-2026-1084",
    title: "Monthly Manufacturing Yield & Tolerance CSV Export",
    type: "Quality Performance",
    generatedDate: "2026-11-01 08:00",
    generatedBy: "QC Lead",
    size: "840 KB",
    status: "Generated",
    format: "CSV",
  },
  {
    id: "REP-2026-1072",
    title: "Powertrain Component Defect Correlation Matrix",
    type: "Defect Analysis",
    generatedDate: "2026-10-25 14:15",
    generatedBy: "Lead Quality Engineer",
    size: "3.1 MB",
    status: "Generated",
    format: "PDF",
  },
];

