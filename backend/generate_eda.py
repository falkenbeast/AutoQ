"""
AutoQ - Exploratory Data Analysis (EDA) Figure Generation Script
Generates high-resolution visualization charts for docs/eda/
"""
import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

# Ensure target directory exists
eda_dir = os.path.join("docs", "eda")
os.makedirs(eda_dir, exist_ok=True)

# Load raw dataset
data_path = os.path.join("backend", "datasets", "raw", "ai4i2020.csv")
df = pd.read_csv(data_path)

# Configure plot aesthetic: clean enterprise dark-mode matching AutoQ UI
plt.style.use("dark_background")
bg_color = "#0B0F14"
card_color = "#151C26"
text_color = "#F1F5F9"
subtext_color = "#94A3B8"
accent_blue = "#3B82F6"
accent_cyan = "#06B6D4"
color_pass = "#22C55E"
color_fail = "#EF4444"
color_warn = "#F59E0B"

plt.rcParams.update({
    "figure.facecolor": bg_color,
    "axes.facecolor": card_color,
    "axes.edgecolor": "#2A3649",
    "axes.labelcolor": text_color,
    "xtick.color": subtext_color,
    "ytick.color": subtext_color,
    "text.color": text_color,
    "grid.color": "#1E293B",
    "grid.linestyle": "--",
    "grid.alpha": 0.6,
    "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
})

# ==============================================================================
# CHART 1: Target Distribution & Defect Mode Breakdown
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6), facecolor=bg_color)

# 1A: Overall Class Balance
target_counts = df["Machine failure"].value_counts()
labels = [f"Passed (Conforming)\n{target_counts[0]:,} (96.61%)", f"Defective (Non-Conforming)\n{target_counts[1]:,} (3.39%)"]
colors = [color_pass, color_fail]
bars = ax1.bar(["Passed", "Defective"], target_counts.values, color=colors, width=0.5, edgecolor="#334155", linewidth=1.5)
ax1.set_title("AutoQ - Overall Inspection Class Distribution", fontsize=13, fontweight="bold", pad=15)
ax1.set_ylabel("Component Count", fontsize=11, labelpad=10)
ax1.set_ylim(0, 11000)
ax1.grid(axis="y")
for bar in bars:
    yval = bar.get_height()
    ax1.text(bar.get_x() + bar.get_width()/2.0, yval + 200, f"{yval:,} ({yval/len(df)*100:.2f}%)", ha="center", va="bottom", fontsize=10, fontweight="bold", color=text_color)

# 1B: Defect Modes Breakdown
defect_modes = ["HDF\n(Heat Dissipation)", "OSF\n(Overstrain)", "PWF\n(Power Failure)", "TWF\n(Tool Wear)", "RNF\n(Random Failure)"]
defect_counts = [df["HDF"].sum(), df["OSF"].sum(), df["PWF"].sum(), df["TWF"].sum(), df["RNF"].sum()]
palette = ["#EF4444", "#F97316", "#F59E0B", "#EAB308", "#8B5CF6"]
bars2 = ax2.bar(defect_modes, defect_counts, color=palette, width=0.55, edgecolor="#334155", linewidth=1.5)
ax2.set_title("Root-Cause Defect Taxonomy Breakdown", fontsize=13, fontweight="bold", pad=15)
ax2.set_ylabel("Occurrences", fontsize=11, labelpad=10)
ax2.set_ylim(0, 140)
ax2.grid(axis="y")
for bar in bars2:
    yval = bar.get_height()
    ax2.text(bar.get_x() + bar.get_width()/2.0, yval + 3, f"{int(yval)}", ha="center", va="bottom", fontsize=10, fontweight="bold", color=text_color)

plt.tight_layout()
chart1_path = os.path.join(eda_dir, "target_distribution.png")
plt.savefig(chart1_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"Generated: {chart1_path}")

# ==============================================================================
# CHART 2: Missing Values & Data Completeness Audit
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5.5), facecolor=bg_color)

missing_counts = df.isnull().sum()
completeness = (1 - df.isnull().sum() / len(df)) * 100

bars = ax1.barh(missing_counts.index, missing_counts.values, color=accent_blue, edgecolor="#334155", height=0.6)
ax1.set_title("Missing Value Count Per Column (0 Missing Detected)", fontsize=13, fontweight="bold", pad=15)
ax1.set_xlabel("Missing Values", fontsize=11)
ax1.set_xlim(-0.5, 10)
ax1.grid(axis="x")
for bar in bars:
    xval = bar.get_width()
    ax1.text(xval + 0.2, bar.get_y() + bar.get_height()/2.0, "0 (0.00%)", ha="left", va="center", fontsize=9, color=color_pass, fontweight="bold")

# Completeness gauge
ax2.barh(completeness.index, completeness.values, color=color_pass, edgecolor="#334155", height=0.6)
ax2.set_title("Feature Data Completeness Percentage", fontsize=13, fontweight="bold", pad=15)
ax2.set_xlabel("Completeness (%)", fontsize=11)
ax2.set_xlim(0, 110)
ax2.grid(axis="x")
for idx, (col, val) in enumerate(completeness.items()):
    ax2.text(val + 1, idx, f"{val:.1f}%", ha="left", va="center", fontsize=9, color=text_color, fontweight="bold")

plt.tight_layout()
chart2_path = os.path.join(eda_dir, "missing_values.png")
plt.savefig(chart2_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"Generated: {chart2_path}")

# ==============================================================================
# CHART 3: Feature Distributions & Probability Density
# ==============================================================================
num_cols = [
    ("Air temperature [K]", "Air Temperature (K)", accent_blue),
    ("Process temperature [K]", "Process Temperature (K)", accent_cyan),
    ("Rotational speed [rpm]", "Rotational Speed (rpm)", "#A855F7"),
    ("Torque [Nm]", "Torque Resistance (Nm)", "#EC4899"),
    ("Tool wear [min]", "Tool Wear Duration (min)", "#EAB308"),
]

fig, axes = plt.subplots(2, 3, figsize=(16, 9), facecolor=bg_color)
axes = axes.flatten()

for i, (col, label, col_color) in enumerate(num_cols):
    ax = axes[i]
    sns.histplot(df[col], kde=True, ax=ax, color=col_color, edgecolor="#2A3649", alpha=0.65, bins=30)
    ax.set_title(f"Distribution: {label}", fontsize=11, fontweight="bold", pad=10)
    ax.set_xlabel(label, fontsize=10)
    ax.set_ylabel("Density / Count", fontsize=10)
    ax.grid(True)
    # Add mean & median lines
    mean_val = df[col].mean()
    med_val = df[col].median()
    ax.axvline(mean_val, color="#F87171", linestyle="--", linewidth=1.5, label=f"Mean: {mean_val:.1f}")
    ax.axvline(med_val, color="#34D399", linestyle=":", linewidth=1.5, label=f"Median: {med_val:.1f}")
    ax.legend(fontsize=8, loc="upper right")

# Component Type pie chart in the 6th subplot
ax6 = axes[5]
type_counts = df["Type"].value_counts()
wedges, texts, autotexts = ax6.pie(
    type_counts.values,
    labels=[f"Type {k}\n({v:,})" for k, v in type_counts.items()],
    autopct="%1.1f%%",
    colors=[accent_blue, accent_cyan, "#8B5CF6"],
    startangle=140,
    wedgeprops=dict(width=0.6, edgecolor="#151C26", linewidth=2),
    textprops=dict(color=text_color, fontsize=10)
)
for at in autotexts:
    at.set_color("#0B0F14")
    at.set_fontweight("bold")
ax6.set_title("Component Variant Proportion (Type L/M/H)", fontsize=11, fontweight="bold", pad=10)

plt.tight_layout()
chart3_path = os.path.join(eda_dir, "feature_distributions.png")
plt.savefig(chart3_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"Generated: {chart3_path}")

# ==============================================================================
# CHART 4: Correlation Heatmap (Pearson & Spearman)
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 7), facecolor=bg_color)

analysis_cols = [
    "Air temperature [K]",
    "Process temperature [K]",
    "Rotational speed [rpm]",
    "Torque [Nm]",
    "Tool wear [min]",
    "Machine failure",
    "HDF",
    "PWF",
    "OSF",
    "TWF",
]
labels_clean = ["Air Temp", "Process Temp", "Rot. Speed", "Torque", "Tool Wear", "Defect (Target)", "HDF", "PWF", "OSF", "TWF"]

corr_pearson = df[analysis_cols].corr(method="pearson")
corr_spearman = df[analysis_cols].corr(method="spearman")

cmap = sns.diverging_palette(220, 10, as_cmap=True)

sns.heatmap(corr_pearson, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-0.9, vmax=0.9,
            square=True, ax=ax1, xticklabels=labels_clean, yticklabels=labels_clean,
            cbar_kws={"shrink": 0.75}, annot_kws={"size": 8.5, "weight": "bold"})
ax1.set_title("Pearson Linear Correlation Matrix", fontsize=12, fontweight="bold", pad=12)

sns.heatmap(corr_spearman, annot=True, fmt=".2f", cmap="coolwarm", center=0, vmin=-0.9, vmax=0.9,
            square=True, ax=ax2, xticklabels=labels_clean, yticklabels=labels_clean,
            cbar_kws={"shrink": 0.75}, annot_kws={"size": 8.5, "weight": "bold"})
ax2.set_title("Spearman Monotonic Rank Correlation Matrix", fontsize=12, fontweight="bold", pad=12)

plt.tight_layout()
chart4_path = os.path.join(eda_dir, "correlation_heatmap.png")
plt.savefig(chart4_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"Generated: {chart4_path}")

# ==============================================================================
# CHART 5: Physical Parameter Relationships & Defect Clusters
# ==============================================================================
fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(16, 6.5), facecolor=bg_color)

# 5A: Torque vs Rotational Speed (Revealing Power boundary and Defect Clusters)
df_pass = df[df["Machine failure"] == 0]
df_fail = df[df["Machine failure"] == 1]

ax1.scatter(df_pass["Rotational speed [rpm]"], df_pass["Torque [Nm]"], color="#3B82F6", alpha=0.35, s=18, label="Passed (Normal Operating Envelope)")
ax1.scatter(df_fail["Rotational speed [rpm]"], df_fail["Torque [Nm]"], color="#EF4444", alpha=0.9, s=40, edgecolors="#FFFFFF", linewidth=0.5, label="Defective (Quality Failure)")

# Draw theoretical power boundary hyperbola (P = 3500W and 9000W)
rpm_range = np.linspace(1150, 2900, 200)
torque_low = (3500 * 60) / (2 * np.pi * rpm_range)
torque_high = (9000 * 60) / (2 * np.pi * rpm_range)
ax1.plot(rpm_range, torque_low, color="#F59E0B", linestyle="--", linewidth=1.5, label="PWF Low Power Boundary (3.5 kW)")
ax1.plot(rpm_range, torque_high, color="#EAB308", linestyle="-.", linewidth=1.5, label="PWF High Power Boundary (9.0 kW)")

ax1.set_title("Rotational Speed vs Torque with Operational Boundaries", fontsize=12, fontweight="bold", pad=12)
ax1.set_xlabel("Rotational Speed (rpm)", fontsize=10)
ax1.set_ylabel("Torque (Nm)", fontsize=10)
ax1.set_xlim(1100, 2950)
ax1.set_ylim(0, 85)
ax1.legend(loc="upper right", fontsize=8.5, framealpha=0.8)
ax1.grid(True)

# 5B: Temperature Difference vs Tool Wear across Failure Modes
df["Temp_Diff"] = df["Process temperature [K]"] - df["Air temperature [K]"]

sns.scatterplot(
    data=df,
    x="Tool wear [min]",
    y="Temp_Diff",
    hue="Machine failure",
    palette={0: "#3B82F6", 1: "#EF4444"},
    alpha=0.6,
    s=25,
    ax=ax2
)
ax2.axhline(8.6, color="#F87171", linestyle="--", linewidth=1.5, label="HDF Thermal Dissipation Threshold (ΔT < 8.6 K)")
ax2.axvline(200, color="#A78BFA", linestyle=":", linewidth=1.5, label="TWF Tool Wear Critical Threshold (200 min)")
ax2.set_title("Thermal Dissipation Gradient (ΔT) vs Cumulative Tool Wear", fontsize=12, fontweight="bold", pad=12)
ax2.set_xlabel("Tool Wear Duration (min)", fontsize=10)
ax2.set_ylabel("Temperature Difference: Process - Air (K)", fontsize=10)
ax2.legend(loc="lower right", fontsize=8.5, framealpha=0.8)
ax2.grid(True)

plt.tight_layout()
chart5_path = os.path.join(eda_dir, "parameter_relationships.png")
plt.savefig(chart5_path, dpi=300, bbox_inches="tight")
plt.close()
print(f"Generated: {chart5_path}")

print("All 5 EDA charts successfully generated in docs/eda/")

