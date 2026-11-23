"""
AutoQ - Architectural Diagram Image Generator
Renders high-resolution, dark-themed industrial diagrams for B.Tech project presentation.
"""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

OUTPUT_DIR = os.path.join("docs", "diagrams")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Styling palette
BG_COLOR = "#0B0F14"
CARD_BG = "#151C26"
CARD_BORDER = "#2A3649"
ACCENT_BLUE = "#3B82F6"
ACCENT_CYAN = "#06B6D4"
TEXT_WHITE = "#F1F5F9"
TEXT_MUTED = "#94A3B8"
GREEN = "#22C55E"
RED = "#EF4444"


def setup_canvas(width=12, height=7, title=""):
    fig, ax = plt.subplots(figsize=(width, height), facecolor=BG_COLOR)
    ax.set_facecolor(BG_COLOR)
    ax.set_xlim(0, 100)
    ax.set_ylim(0, 100)
    ax.axis("off")
    if title:
        fig.suptitle(title, fontsize=18, fontweight="bold", color=TEXT_WHITE, y=0.96)
    return fig, ax


def draw_box(ax, x, y, w, h, title, subtitle="", bg=CARD_BG, border=CARD_BORDER, text_col=TEXT_WHITE, radius=1.5):
    rect = patches.FancyBboxPatch(
        (x, y), w, h,
        boxstyle=f"round,pad=0.5,rounding_size={radius}",
        facecolor=bg, edgecolor=border, linewidth=1.5, zorder=2
    )
    ax.add_patch(rect)
    if subtitle:
        ax.text(x + w / 2, y + h * 0.62, title, ha="center", va="center", color=text_col, fontsize=11, fontweight="bold", zorder=3)
        ax.text(x + w / 2, y + h * 0.32, subtitle, ha="center", va="center", color=TEXT_MUTED, fontsize=8.5, zorder=3)
    else:
        ax.text(x + w / 2, y + h / 2, title, ha="center", va="center", color=text_col, fontsize=10.5, fontweight="bold", zorder=3)


def draw_arrow(ax, x1, y1, x2, y2, label="", color=ACCENT_BLUE):
    ax.annotate(
        "", xy=(x2, y2), xytext=(x1, y1),
        arrowprops=dict(arrowstyle="-|>", color=color, lw=2, mutation_scale=15),
        zorder=4
    )
    if label:
        ax.text((x1 + x2) / 2, (y1 + y2) / 2 + 1.8, label, ha="center", va="bottom", color=TEXT_MUTED, fontsize=8, zorder=5)


# 1. Overall System Architecture
def render_system_architecture():
    fig, ax = setup_canvas(14, 8, "AutoQ: Overall System Architecture")
    
    # Client Layer
    ax.text(50, 88, "PRESENTATION LAYER (React 19 + Vite + Tailwind CSS)", ha="center", color=ACCENT_CYAN, fontsize=12, fontweight="bold")
    draw_box(ax, 5, 74, 16, 10, "Overview Dashboard", "KPIs & Recharts")
    draw_box(ax, 23.5, 74, 16, 10, "Inspection Manager", "CRUD & Cataloging")
    draw_box(ax, 42, 74, 16, 10, "Prediction Studio", "Real-Time Inference")
    draw_box(ax, 60.5, 74, 16, 10, "Quality Analytics", "Trends & Batches")
    draw_box(ax, 79, 74, 16, 10, "Audit Reports", "PDF / CSV Downloads")

    # API Layer
    ax.text(50, 58, "APPLICATION & SERVICE LAYER (FastAPI Asynchronous Gateway)", ha="center", color=ACCENT_BLUE, fontsize=12, fontweight="bold")
    draw_box(ax, 10, 44, 23, 10, "REST Router", "Contract Parity /api & /api/v1")
    draw_box(ax, 38.5, 44, 23, 10, "Business Services", "Inspection, Prediction, Analytics")
    draw_box(ax, 67, 44, 23, 10, "ReportLab Engine", "Dynamic PDF & CSV Generation")

    # Bottom Layers
    ax.text(25, 28, "PERSISTENCE TIER", ha="center", color=GREEN, fontsize=11, fontweight="bold")
    draw_box(ax, 8, 12, 34, 12, "SQLite Database (autoq.db)", "Foreign Keys ON | ACID Compliant | 4 Tables")

    ax.text(75, 28, "MACHINE LEARNING TIER", ha="center", color="#A855F7", fontsize=11, fontweight="bold")
    draw_box(ax, 58, 12, 34, 12, "Serialized ML Artifacts", "Random Forest (v1.0.0) | Multi-class Classifier")

    # Connectors
    draw_arrow(ax, 50, 74, 50, 55, "HTTP / JSON REST API")
    draw_arrow(ax, 25, 44, 25, 25, "SQLAlchemy ORM")
    draw_arrow(ax, 75, 44, 75, 25, "Joblib Pipelines")

    fig.savefig(os.path.join(OUTPUT_DIR, "system_architecture.png"), dpi=200, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)


# 2. Prediction Workflow
def render_prediction_workflow():
    fig, ax = setup_canvas(14, 7, "AutoQ: Real-Time Defect Prediction Workflow")

    draw_box(ax, 3, 40, 16, 20, "1. Input Telemetry", "Speed, Torque, Wear,\nPressure, Temp", border=ACCENT_CYAN)
    draw_box(ax, 23, 40, 16, 20, "2. Feature Mapping", "Compute ΔT, Power,\nOverstrain Index", border=ACCENT_BLUE)
    draw_box(ax, 43, 40, 16, 20, "3. Champion Pipeline", "Random Forest Classifier\nROC-AUC: 0.9830", border="#A855F7")
    draw_box(ax, 63, 52, 16, 18, "4a. Defect Detected", "p >= τ (Threshold)\nReject Component", border=RED)
    draw_box(ax, 63, 22, 16, 18, "4b. Conforming Part", "p < τ (Threshold)\nPass Component", border=GREEN)
    draw_box(ax, 83, 52, 14, 18, "5. Failure Mode", "Heat / Power /\nOverstrain / Wear", border=RED)
    draw_box(ax, 83, 22, 14, 18, "6. Persistence", "Save in SQLite\npredictions table", border=ACCENT_BLUE)

    draw_arrow(ax, 19, 50, 23, 50)
    draw_arrow(ax, 39, 50, 43, 50)
    draw_arrow(ax, 59, 53, 63, 61, "p >= 0.50")
    draw_arrow(ax, 59, 47, 63, 31, "p < 0.50")
    draw_arrow(ax, 79, 61, 83, 61)
    draw_arrow(ax, 79, 31, 83, 31)

    fig.savefig(os.path.join(OUTPUT_DIR, "prediction_workflow.png"), dpi=200, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)


# 3. Database ERD
def render_database_erd():
    fig, ax = setup_canvas(13, 7, "AutoQ: Database Entity Relationship Diagram (autoq.db)")

    draw_box(ax, 5, 52, 26, 32, "COMPONENTS", "PK: id (Integer)\nUK: component_id (String)\ncomponent_name (String)\ncomponent_category (String)\ndescription (Text)", border=ACCENT_CYAN)
    draw_box(ax, 40, 52, 26, 32, "INSPECTIONS", "PK: id (Integer)\nFK: component_id (String)\nmanufacturing_temp (Float)\npressure (Float)\nproduction_batch (String)\ninspection_result (String)", border=ACCENT_BLUE)
    draw_box(ax, 75, 52, 22, 32, "REPORTS", "PK: id (Integer)\nUK: report_code (String)\ntitle (String)\nfile_type (String: PDF/CSV)\nfile_path (String)\nstatus (String)", border=GREEN)
    draw_box(ax, 22, 10, 32, 30, "PREDICTIONS", "PK: id (Integer)\nFK: component_id (Nullable)\nFK: inspection_id (Nullable, Decoupled)\npredicted_status (String)\ndefect_probability (Float)\nmodel_version (String: 1.0.0)\ncontributing_factors (JSON)", border="#A855F7")

    draw_arrow(ax, 31, 68, 40, 68, "1 : N")
    draw_arrow(ax, 18, 52, 28, 40, "1 : N")
    draw_arrow(ax, 53, 52, 45, 40, "1 : 1 (Nullable)")

    fig.savefig(os.path.join(OUTPUT_DIR, "database_erd.png"), dpi=200, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)


# 4. ML Pipeline Diagram
def render_ml_pipeline():
    fig, ax = setup_canvas(14, 6.5, "AutoQ: Machine Learning Training & Evaluation Pipeline")

    draw_box(ax, 4, 35, 16, 25, "1. Industrial Telemetry", "AI4I 2020 Benchmark\n10,000 Total Records\n3.48% Defect Imbalance", border=ACCENT_CYAN)
    draw_box(ax, 24, 35, 16, 25, "2. Zero-Leakage Split", "Stratified 80/20 Partition\nTrain: 8,000 (280 defects)\nTest: 2,000 (68 defects)", border=ACCENT_BLUE)
    draw_box(ax, 44, 35, 16, 25, "3. Feature Engineering", "ΔT = T_proc - T_air\nP_mech = 2π*Speed*Torque\nOverstrain = Wear * Torque", border="#A855F7")
    draw_box(ax, 64, 35, 16, 25, "4. 5-Fold Stratified CV", "Trained: RF, GBM, LR, DT\nCost-sensitive weighting\nOptimized for Recall", border=ACCENT_BLUE)
    draw_box(ax, 84, 35, 14, 25, "5. Champion Selection", "Balanced Random Forest\nROC-AUC: 0.9830\nDefect Recall: 86.76%", border=GREEN)

    draw_arrow(ax, 20, 47.5, 24, 47.5)
    draw_arrow(ax, 40, 47.5, 44, 47.5)
    draw_arrow(ax, 60, 47.5, 64, 47.5)
    draw_arrow(ax, 80, 47.5, 84, 47.5)

    fig.savefig(os.path.join(OUTPUT_DIR, "ml_training_pipeline.png"), dpi=200, bbox_inches="tight", facecolor=BG_COLOR)
    plt.close(fig)


if __name__ == "__main__":
    print("Generating AutoQ architecture diagram images...")
    render_system_architecture()
    render_prediction_workflow()
    render_database_erd()
    render_ml_pipeline()
    print("All architecture diagram images generated successfully in docs/diagrams/.")

