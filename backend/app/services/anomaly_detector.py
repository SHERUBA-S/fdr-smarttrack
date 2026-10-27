import numpy as np
import os
import joblib
import logging
from typing import Dict, Any, Optional, Tuple, List
from decimal import Decimal
from sklearn.ensemble import IsolationForest
from app.models.fdr import FDRRecord

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../data/anomaly_model.joblib"))

class AnomalyDetector:
    """
    Experimental Machine Learning Anomaly Detection service using scikit-learn IsolationForest.
    Provides review-priority risk ranking for administrative oversight.
    """
    _model: Optional[IsolationForest] = None

    @classmethod
    def get_feature_schema(cls) -> List[str]:
        return [
            "log_principal_amount",
            "tenure_days",
            "interest_rate",
            "ref_length",
            "has_discrepancy_int"
        ]

    @classmethod
    def extract_features(cls, fdr: FDRRecord) -> np.ndarray:
        """Extract numerical feature vector from an FDRRecord."""
        # 1. Log of principal amount to handle skewed monetary values
        amt = float(fdr.principal_amount) if fdr.principal_amount else 100000.0
        log_amt = float(np.log1p(max(amt, 1.0)))

        # 2. Tenure in days
        if fdr.issue_date and fdr.maturity_date:
            tenure = float((fdr.maturity_date - fdr.issue_date).days)
        else:
            tenure = 365.0

        # 3. Interest rate
        rate = float(fdr.interest_rate) if fdr.interest_rate else 6.5

        # 4. Length of reference number
        ref_len = float(len(fdr.fdr_number)) if fdr.fdr_number else 10.0

        # 5. Discrepancy indicator
        disc = 1.0 if fdr.has_discrepancy else 0.0

        return np.array([[log_amt, tenure, rate, ref_len, disc]], dtype=np.float32)

    @classmethod
    def load_or_train_baseline(cls) -> IsolationForest:
        """Load saved model or train a baseline model on synthetic reference distributions."""
        if cls._model is not None:
            return cls._model

        if os.path.exists(MODEL_PATH):
            try:
                cls._model = joblib.load(MODEL_PATH)
                logger.info("Loaded pre-trained IsolationForest model from disk.")
                return cls._model
            except Exception as e:
                logger.warning(f"Could not load model file, retraining: {e}")

        # Train a synthetic baseline model
        np.random.seed(42)
        n_samples = 1500
        # Realistic amounts: log-normal around ₹5 Lakh to ₹50 Lakh
        log_amounts = np.random.normal(13.8, 1.2, n_samples)
        # Normal tenure: 365 to 1095 days (1 to 3 years)
        tenures = np.random.normal(730, 250, n_samples)
        tenures = np.clip(tenures, 90, 3650)
        # Interest rates: 6.0% to 8.5%
        rates = np.random.normal(7.2, 0.8, n_samples)
        rates = np.clip(rates, 4.0, 12.0)
        # Ref length: 8 to 18 characters
        ref_lens = np.random.normal(12, 2.5, n_samples)
        ref_lens = np.clip(ref_lens, 6, 25)
        # Discrepancy: ~5% naturally occurring
        discrepancies = np.random.choice([0.0, 1.0], size=n_samples, p=[0.95, 0.05])

        X_train = np.column_stack([log_amounts, tenures, rates, ref_lens, discrepancies])

        model = IsolationForest(
            n_estimators=100,
            contamination=0.05,
            random_state=42
        )
        model.fit(X_train)
        cls._model = model

        # Ensure directory exists and save
        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        try:
            joblib.dump(model, MODEL_PATH)
            logger.info(f"Trained and saved baseline anomaly model to {MODEL_PATH}")
        except Exception as e:
            logger.warning(f"Could not save anomaly model: {e}")

        return cls._model

    @classmethod
    def evaluate_fdr(cls, fdr: FDRRecord) -> Tuple[float, str]:
        """
        Score an FDR record.
        Returns:
            (anomaly_score, explanation_signal)
            anomaly_score: float from 0.0 (normal) to 1.0 (highest review priority)
        """
        model = cls.load_or_train_baseline()
        features = cls.extract_features(fdr)

        try:
            # decision_function gives negative values for anomalies, positive for normal
            raw_score = model.decision_function(features)[0]
            # Normalize to 0.0 - 1.0 where higher means higher anomaly / review priority
            # Typical raw_score is in [-0.3, 0.2]
            normalized = float(np.clip(1.0 - (raw_score + 0.3) / 0.5, 0.0, 1.0))
        except Exception:
            normalized = 0.5 if fdr.has_discrepancy else 0.1

        # Generate human-readable review signal explanation
        reasons = []
        if fdr.principal_amount and fdr.principal_amount > Decimal("50000000"):
            reasons.append("Very high principal amount (> ₹5 Crore)")
        if fdr.issue_date and fdr.maturity_date:
            tenure_days = (fdr.maturity_date - fdr.issue_date).days
            if tenure_days < 90 or tenure_days > 2500:
                reasons.append(f"Unusual tenure length ({tenure_days} days)")
        if fdr.interest_rate and (fdr.interest_rate > Decimal("10.0") or fdr.interest_rate < Decimal("4.0")):
            reasons.append(f"Atypical interest rate ({fdr.interest_rate}%)")
        if fdr.has_discrepancy:
            reasons.append("Field discrepancy detected in document verification")

        if not reasons:
            signal = "Parameters align with normal institutional security deposit baseline."
        else:
            signal = "Priority Review Recommended: " + "; ".join(reasons)

        return round(normalized, 3), signal
