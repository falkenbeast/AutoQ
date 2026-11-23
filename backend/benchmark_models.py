"""
AutoQ - ML Model Development & Benchmark Script
Evaluates 4 Scikit-learn algorithms with stratified 5-fold CV and holdout test set:
1. Logistic Regression
2. Decision Tree Classifier
3. Random Forest Classifier
4. Gradient Boosting Classifier
"""
import sys
import os
import time
import pandas as pd
import numpy as np

# Set environment
backend_dir = os.path.dirname(os.path.abspath(__file__))
if backend_dir not in sys.path:
    sys.path.insert(0, backend_dir)

from sklearn.linear_model import LogisticRegression
from sklearn.tree import DecisionTreeClassifier
from sklearn.ensemble import RandomForestClassifier, GradientBoostingClassifier
from sklearn.pipeline import Pipeline
from sklearn.model_selection import StratifiedKFold, cross_validate
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score, f1_score,
    roc_auc_score, average_precision_score, confusion_matrix,
    classification_report, brier_score_loss
)
import joblib
from app.ml.training.data import TrainingDataLoader

loader = TrainingDataLoader()
X_train, X_test, y_train, y_test, y_train_multi, y_test_multi = loader.load_data()

# Load the fitted preprocessor from Phase 5
preprocessor_path = os.path.join("backend", "trained_models", "preprocessor.joblib")
preprocessor = joblib.load(preprocessor_path)

print(f"Loaded Train: {X_train.shape}, Test: {X_test.shape}")
print(f"Train defects: {y_train.sum()} ({y_train.mean()*100:.2f}%), Test defects: {y_test.sum()} ({y_test.mean()*100:.2f}%)")

# Define Candidate Models with class weighting to handle manufacturing class imbalance
candidate_models = {
    "Logistic Regression": Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", LogisticRegression(
            class_weight="balanced",
            C=1.0,
            max_iter=1000,
            random_state=42,
            solver="lbfgs"
        ))
    ]),
    "Decision Tree": Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", DecisionTreeClassifier(
            class_weight="balanced",
            max_depth=6,
            min_samples_split=10,
            min_samples_leaf=5,
            random_state=42
        ))
    ]),
    "Random Forest": Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", RandomForestClassifier(
            n_estimators=150,
            class_weight="balanced",
            max_depth=10,
            min_samples_split=8,
            min_samples_leaf=3,
            random_state=42,
            n_jobs=-1
        ))
    ]),
    "Gradient Boosting": Pipeline([
        ("preprocessor", preprocessor),
        ("classifier", GradientBoostingClassifier(
            n_estimators=150,
            learning_rate=0.08,
            max_depth=4,
            subsample=0.85,
            random_state=42
        ))
    ])
}

cv = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
scoring = ["roc_auc", "f1", "recall", "precision", "accuracy"]

results = []

for name, pipe in candidate_models.items():
    print(f"\nEvaluating {name}...")
    start_time = time.time()
    
    # 1. Stratified 5-Fold Cross Validation on Training Set Only
    cv_out = cross_validate(pipe, X_train, y_train, cv=cv, scoring=scoring, n_jobs=-1)
    train_duration = time.time() - start_time
    
    # 2. Fit on full training set
    pipe.fit(X_train, y_train)
    
    # 3. Predict on unseen holdout test set
    y_pred = pipe.predict(X_test)
    y_prob = pipe.predict_proba(X_test)[:, 1] if hasattr(pipe, "predict_proba") else None
    
    acc = accuracy_score(y_test, y_pred)
    prec = precision_score(y_test, y_pred, zero_division=0)
    rec = recall_score(y_test, y_pred)
    f1 = f1_score(y_test, y_pred)
    roc_auc = roc_auc_score(y_test, y_prob) if y_prob is not None else 0.0
    pr_auc = average_precision_score(y_test, y_prob) if y_prob is not None else 0.0
    brier = brier_score_loss(y_test, y_prob) if y_prob is not None else 0.0
    
    cm = confusion_matrix(y_test, y_pred)
    tn, fp, fn, tp = cm.ravel()
    
    print(f"  CV ROC-AUC: {cv_out['test_roc_auc'].mean():.4f} (+/- {cv_out['test_roc_auc'].std():.4f})")
    print(f"  CV F1:      {cv_out['test_f1'].mean():.4f} (+/- {cv_out['test_f1'].std():.4f})")
    print(f"  CV Recall:  {cv_out['test_recall'].mean():.4f} (+/- {cv_out['test_recall'].std():.4f})")
    print(f"  Test Metrics: Acc={acc:.4f}, Prec={prec:.4f}, Rec={rec:.4f}, F1={f1:.4f}, ROC-AUC={roc_auc:.4f}, PR-AUC={pr_auc:.4f}")
    print(f"  Confusion Matrix: TN={tn}, FP={fp}, FN={fn}, TP={tp}")
    print(f"  Brier Score: {brier:.4f}")
    
    results.append({
        "Model": name,
        "CV_ROC_AUC": cv_out["test_roc_auc"].mean(),
        "CV_ROC_AUC_std": cv_out["test_roc_auc"].std(),
        "CV_F1": cv_out["test_f1"].mean(),
        "CV_Recall": cv_out["test_recall"].mean(),
        "CV_Precision": cv_out["test_precision"].mean(),
        "Test_Accuracy": acc,
        "Test_Precision": prec,
        "Test_Recall": rec,
        "Test_F1": f1,
        "Test_ROC_AUC": roc_auc,
        "Test_PR_AUC": pr_auc,
        "Test_Brier": brier,
        "TN": tn,
        "FP": fp,
        "FN": fn,
        "TP": tp,
        "Train_Duration_Sec": train_duration
    })

res_df = pd.DataFrame(results)
print("\n" + "="*80)
print("FINAL BENCHMARK COMPARISON TABLE")
print("="*80)
print(res_df[["Model", "CV_ROC_AUC", "CV_Recall", "Test_Recall", "Test_Precision", "Test_F1", "Test_ROC_AUC", "FN", "TP"]].to_string(index=False))

