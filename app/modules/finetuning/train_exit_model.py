"""Train and tune the Exit Advisor classifier (Lesson 15 GridSearchCV)."""

import sys
from pathlib import Path

import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score
from sklearn.model_selection import GridSearchCV, train_test_split
from sklearn.pipeline import Pipeline

ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from app.modules.config import EXIT_MODEL_PATH, MODELS_DIR
from app.modules.finetuning.prepare_data import build_labeled_rows


def train_exit_model(output_path=EXIT_MODEL_PATH, random_state=42):
    frame = build_labeled_rows()
    if frame.empty:
        raise ValueError("No labeled turns were found.")

    x = frame["history"].fillna("")
    y = frame["end_label"]

    x_train, x_test, y_train, y_test = train_test_split(
        x,
        y,
        test_size=0.3,
        random_state=random_state,
        stratify=y,
    )

    pipeline = Pipeline(
        [
            ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
            ("clf", LogisticRegression(max_iter=1000)),
        ]
    )
    param_grid = {
        "tfidf__ngram_range": [(1, 1), (1, 2)],
        "clf__C": [0.5, 1.0, 2.0],
    }
    search = GridSearchCV(pipeline, param_grid, cv=3, scoring="accuracy")
    search.fit(x_train, y_train)

    y_pred = search.predict(x_test)
    test_accuracy = accuracy_score(y_test, y_pred)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(search.best_estimator_, output_path)

    print("Best parameters:", search.best_params_)
    print(f"CV accuracy: {search.best_score_:.3f}")
    print(f"Test accuracy: {test_accuracy:.3f}")
    print(f"Saved model to {output_path}")
    return search.best_estimator_, test_accuracy


if __name__ == "__main__":
    train_exit_model()
