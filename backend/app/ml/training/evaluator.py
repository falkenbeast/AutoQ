"""
AutoQ - Model Evaluation and Visualization Module
Generates comprehensive evaluation metrics, confusion matrices, ROC curves,
Precision-Recall curves, feature importance charts, and model comparison figures.
"""
import os
import matplotlib
matplotlib.use("Agg")
from typing import Any, Dict, List, Tuple
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import seaborn as sns
from sklearn.inspection import permutation_importance
from sklearn.metrics import (
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    confusion_matrix,
    f1_score,
    precision_recall_curve,
    precision_score,
    recall_score,
    roc_auc_score,
    roc_curve,
)


class ModelEvaluator:
    """
    Evaluates trained candidate pipelines on holdout testing data and generates
    high-resolution diagnostic visualization charts.
    """

    def __init__(self, output_dir: str = os.path.join("docs", "model_evaluation")):
        self.output_dir = output_dir
        os.makedirs(output_dir, exist_ok=True)

        # Dark theme aesthetic matching AutoQ
        self.bg_color = "#0B0F14"
        self.card_color = "#151C26"
        self.text_color = "#F1F5F9"
        self.subtext_color = "#94A3B8"
        self.accent_blue = "#3B82F6"
        self.accent_cyan = "#06B6D4"
        self.color_pass = "#22C55E"
        self.color_fail = "#EF4444"

        plt.style.use("dark_background")
        plt.rcParams.update({
            "figure.facecolor": self.bg_color,
            "axes.facecolor": self.card_color,
            "axes.edgecolor": "#2A3649",
            "axes.labelcolor": self.text_color,
            "xtick.color": self.subtext_color,
            "ytick.color": self.subtext_color,
            "text.color": self.text_color,
            "grid.color": "#1E293B",
            "grid.linestyle": "--",
            "grid.alpha": 0.6,
            "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Helvetica", "Arial"],
        })

    def evaluate_model(
        self,
        name: str,
        pipeline: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series,
    ) -> Dict[str, Any]:
        """Calculates exhaustive classification performance metrics on unseen holdout test set."""
        y_pred = pipeline.predict(X_test)
        y_prob = pipeline.predict_proba(X_test)[:, 1] if hasattr(pipeline, "predict_proba") else None

        acc = float(accuracy_score(y_test, y_pred))
        prec = float(precision_score(y_test, y_pred, zero_division=0))
        rec = float(recall_score(y_test, y_pred))
        f1 = float(f1_score(y_test, y_pred))
        roc_auc = float(roc_auc_score(y_test, y_prob)) if y_prob is not None else 0.0
        pr_auc = float(average_precision_score(y_test, y_prob)) if y_prob is not None else 0.0
        brier = float(brier_score_loss(y_test, y_prob)) if y_prob is not None else 0.0

        cm = confusion_matrix(y_test, y_pred)
        tn, fp, fn, tp = [int(v) for v in cm.ravel()]

        return {
            "model_name": name,
            "accuracy": round(acc, 4),
            "precision": round(prec, 4),
            "recall": round(rec, 4),
            "f1_score": round(f1, 4),
            "roc_auc": round(roc_auc, 4),
            "pr_auc": round(pr_auc, 4),
            "brier_score": round(brier, 4),
            "confusion_matrix": {
                "true_negative": tn,
                "false_positive": fp,
                "false_negative": fn,
                "true_positive": tp,
            },
            "y_pred": y_pred,
            "y_prob": y_prob,
        }

    def generate_all_plots(
        self,
        eval_results: Dict[str, Dict[str, Any]],
        champion_name: str,
        champion_pipeline: Any,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        feature_names: List[str],
    ) -> List[str]:
        """Renders and saves all 5 required model evaluation charts."""
        created_paths = []
        created_paths.append(self.plot_confusion_matrices(eval_results, champion_name, y_test))
        created_paths.append(self.plot_roc_curves(eval_results, y_test))
        created_paths.append(self.plot_precision_recall_curves(eval_results, y_test))
        created_paths.append(self.plot_model_comparison(eval_results))
        created_paths.append(
            self.plot_feature_importance(
                champion_pipeline, champion_name, X_test, y_test, feature_names
            )
        )
        return created_paths

    def plot_confusion_matrices(
        self,
        eval_results: Dict[str, Dict[str, Any]],
        champion_name: str,
        y_test: pd.Series,
    ) -> str:
        """Renders 2x2 grid of confusion matrices across all candidate models."""
        fig, axes = plt.subplots(2, 2, figsize=(13, 11), facecolor=self.bg_color)
        axes = axes.flatten()

        for idx, (name, metrics) in enumerate(eval_results.items()):
            ax = axes[idx]
            cm = np.array([
                [metrics["confusion_matrix"]["true_negative"], metrics["confusion_matrix"]["false_positive"]],
                [metrics["confusion_matrix"]["false_negative"], metrics["confusion_matrix"]["true_positive"]],
            ])

            # Annotate with percentages
            annot = np.empty_like(cm, dtype=object)
            annot[0, 0] = f"TN: {cm[0, 0]}\n({cm[0, 0]/cm[0].sum()*100:.1f}%)"
            annot[0, 1] = f"FP: {cm[0, 1]}\n(False Alarm)"
            annot[1, 0] = f"FN: {cm[1, 0]}\n(Critical Escape!)"
            annot[1, 1] = f"TP: {cm[1, 1]}\n({cm[1, 1]/cm[1].sum()*100:.1f}%)"

            is_champ = (name == champion_name)
            border_color = self.accent_cyan if is_champ else "#334155"

            sns.heatmap(
                cm,
                annot=annot,
                fmt="",
                cmap="Blues",
                cbar=False,
                ax=ax,
                linewidths=1.5,
                linecolor="#151C26",
                annot_kws={"size": 11, "weight": "bold"},
            )

            title_suffix = " [Selected Champion]" if is_champ else ""
            ax.set_title(f"{name}{title_suffix}", fontsize=12, fontweight="bold", pad=10, color=self.text_color)
            ax.set_xlabel("Predicted Quality State", fontsize=10)
            ax.set_ylabel("True Inspection Label", fontsize=10)
            ax.set_xticklabels(["Passed", "Defective"], fontsize=9.5)
            ax.set_yticklabels(["Passed", "Defective"], fontsize=9.5)

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "confusion_matrix.png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        return out_path

    def plot_roc_curves(
        self,
        eval_results: Dict[str, Dict[str, Any]],
        y_test: pd.Series,
    ) -> str:
        """Renders comparative Receiver Operating Characteristic (ROC) curves."""
        fig, ax = plt.subplots(figsize=(10, 7), facecolor=self.bg_color)
        colors = ["#3B82F6", "#06B6D4", "#EAB308", "#EC4899"]

        for idx, (name, metrics) in enumerate(eval_results.items()):
            y_prob = metrics["y_prob"]
            if y_prob is None:
                continue
            fpr, tpr, _ = roc_curve(y_test, y_prob)
            roc_auc = metrics["roc_auc"]
            ax.plot(
                fpr,
                tpr,
                color=colors[idx % len(colors)],
                linewidth=2.2,
                label=f"{name} (AUC = {roc_auc:.4f})",
            )

        # Baseline diagonal
        ax.plot([0, 1], [0, 1], color="#64748B", linestyle="--", linewidth=1.2, label="Random Guess (AUC = 0.5000)")

        ax.set_title("AutoQ - Receiver Operating Characteristic (ROC) Comparison", fontsize=13, fontweight="bold", pad=15)
        ax.set_xlabel("False Positive Rate (1 - Specificity)", fontsize=11, labelpad=10)
        ax.set_ylabel("True Positive Rate (Defect Recall)", fontsize=11, labelpad=10)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.grid(True)
        ax.legend(loc="lower right", fontsize=10, framealpha=0.85)

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "roc_curve.png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        return out_path

    def plot_precision_recall_curves(
        self,
        eval_results: Dict[str, Dict[str, Any]],
        y_test: pd.Series,
    ) -> str:
        """Renders Precision-Recall curves, critical for imbalanced manufacturing defects."""
        fig, ax = plt.subplots(figsize=(10, 7), facecolor=self.bg_color)
        colors = ["#3B82F6", "#06B6D4", "#EAB308", "#EC4899"]

        no_skill = y_test.mean()
        ax.axhline(no_skill, color="#64748B", linestyle="--", linewidth=1.2, label=f"No Skill Baseline (PR = {no_skill:.4f})")

        for idx, (name, metrics) in enumerate(eval_results.items()):
            y_prob = metrics["y_prob"]
            if y_prob is None:
                continue
            precision, recall, _ = precision_recall_curve(y_test, y_prob)
            pr_auc = metrics["pr_auc"]
            ax.plot(
                recall,
                precision,
                color=colors[idx % len(colors)],
                linewidth=2.2,
                label=f"{name} (PR-AUC = {pr_auc:.4f})",
            )

        ax.set_title("AutoQ - Precision-Recall Curve (Minority Defect Class)", fontsize=13, fontweight="bold", pad=15)
        ax.set_xlabel("Recall (Fraction of Defects Detected)", fontsize=11, labelpad=10)
        ax.set_ylabel("Precision (Fraction of Flagged Parts Actually Defective)", fontsize=11, labelpad=10)
        ax.set_xlim(-0.02, 1.02)
        ax.set_ylim(-0.02, 1.02)
        ax.grid(True)
        ax.legend(loc="upper right", fontsize=10, framealpha=0.85)

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "precision_recall_curve.png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        return out_path

    def plot_model_comparison(
        self,
        eval_results: Dict[str, Dict[str, Any]],
    ) -> str:
        """Renders grouped bar chart comparing Accuracy, Recall, Precision, F1, and ROC-AUC."""
        fig, ax = plt.subplots(figsize=(13, 6.5), facecolor=self.bg_color)

        models = list(eval_results.keys())
        metrics_keys = ["recall", "precision", "f1_score", "roc_auc"]
        metrics_labels = ["Defect Recall", "Precision", "F1-Score", "ROC-AUC"]
        metric_colors = [self.color_fail, self.accent_blue, "#EAB308", self.accent_cyan]

        x = np.arange(len(models))
        width = 0.18

        for i, (m_key, m_label, col) in enumerate(zip(metrics_keys, metrics_labels, metric_colors)):
            vals = [eval_results[m][m_key] for m in models]
            bars = ax.bar(x + (i - 1.5) * width, vals, width, label=m_label, color=col, edgecolor="#334155", linewidth=1.2)
            for bar in bars:
                height = bar.get_height()
                ax.annotate(
                    f"{height:.2f}",
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3),
                    textcoords="offset points",
                    ha="center",
                    va="bottom",
                    fontsize=8,
                    fontweight="bold",
                )

        ax.set_title("AutoQ - Machine Learning Model Performance Comparison", fontsize=13, fontweight="bold", pad=15)
        ax.set_ylabel("Score (0.0 to 1.0)", fontsize=11, labelpad=10)
        ax.set_xticks(x)
        ax.set_xticklabels(models, fontsize=10.5, fontweight="bold")
        ax.set_ylim(0, 1.15)
        ax.grid(axis="y")
        ax.legend(loc="upper right", fontsize=9.5, framealpha=0.85)

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "model_comparison.png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        return out_path

    def plot_feature_importance(
        self,
        pipeline: Any,
        model_name: str,
        X_test: pd.DataFrame,
        y_test: pd.Series,
        feature_names: List[str],
    ) -> str:
        """
        Renders Random Forest MDI Feature Importance and Test Permutation Importance.
        Contrasts predictive association with physical causation.
        """
        fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6.5), facecolor=self.bg_color)

        classifier = pipeline.named_steps["classifier"]
        
        # 1. Tree Mean Decrease in Impurity (MDI) Importance
        if hasattr(classifier, "feature_importances_"):
            importances = classifier.feature_importances_
            clean_names = [f.replace("_", " ").title() for f in feature_names]
            indices = np.argsort(importances)

            ax1.barh(
                range(len(indices)),
                importances[indices],
                color=self.accent_blue,
                edgecolor="#334155",
                align="center",
            )
            ax1.set_yticks(range(len(indices)))
            ax1.set_yticklabels([clean_names[i] for i in indices], fontsize=9.5)
            ax1.set_xlabel("Relative Gini Importance", fontsize=10)
            ax1.set_title(f"{model_name} - Gini Feature Importance (MDI)", fontsize=11.5, fontweight="bold", pad=12)
            ax1.grid(axis="x")

        # 2. Permutation Importance on holdout test set
        perm = permutation_importance(pipeline, X_test, y_test, n_repeats=10, random_state=42, n_jobs=-1)
        perm_mean = perm.importances_mean
        perm_indices = np.argsort(perm_mean)

        # Map to original features (X_test has original column names)
        x_cols = [c.replace("_", " ").title() for c in X_test.columns]

        ax2.barh(
            range(len(perm_indices)),
            perm_mean[perm_indices],
            color=self.accent_cyan,
            edgecolor="#334155",
            align="center",
        )
        ax2.set_yticks(range(len(perm_indices)))
        ax2.set_yticklabels([x_cols[i] for i in perm_indices], fontsize=9.5)
        ax2.set_xlabel("Mean Test Accuracy Degradation on Shuffle", fontsize=10)
        ax2.set_title("Test Permutation Importance (Predictive Impact)", fontsize=11.5, fontweight="bold", pad=12)
        ax2.grid(axis="x")

        plt.tight_layout()
        out_path = os.path.join(self.output_dir, "feature_importance.png")
        plt.savefig(out_path, dpi=300, bbox_inches="tight")
        plt.close()
        return out_path
