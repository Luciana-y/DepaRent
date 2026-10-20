"""Entrena el clustering productivo de RF1 (sin variables de precio).

Uso (desde cualquier directorio):
    python deliveries/week10/code/scripts/train_clustering.py            # solo evalúa k=2..6
    python deliveries/week10/code/scripts/train_clustering.py --k 3      # evalúa y guarda el modelo k=3

Sin --k no se escribe ningún artefacto: la elección de k se hace revisando la evaluación.
"""
import argparse
import json
import platform
import sys
from datetime import datetime, timezone
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

import joblib  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402
import scipy  # noqa: E402
import sklearn  # noqa: E402
from sklearn.cluster import KMeans  # noqa: E402
from sklearn.metrics import adjusted_rand_score, silhouette_score  # noqa: E402
from sklearn.pipeline import Pipeline  # noqa: E402
from sklearn.preprocessing import StandardScaler  # noqa: E402

from config import MODELS_DIR, find_data_file  # noqa: E402
from src.clustering import (  # noqa: E402
    EXCLUDED_FEATURES, FEATURES, METADATA_FILE, PIPELINE_FILE, PRICE_COLUMNS, SOURCE_FILE,
    ClusteringPreprocessor, build_cluster_profiles, load_training_frame, sha256_of,
)
from src.input_validation import RANGES  # noqa: E402

RANDOM_STATE = 42
N_INIT = 10
K_RANGE = range(2, 7)
SEEDS = [0, 1, 7, 42, 123, 2024]
N_SUBSAMPLES = 10
SUBSAMPLE_FRAC = 0.8


def make_pipeline(k, random_state=RANDOM_STATE):
    return Pipeline([
        ("prep", ClusteringPreprocessor()),
        ("scaler", StandardScaler()),
        ("kmeans", KMeans(n_clusters=k, random_state=random_state, n_init=N_INIT)),
    ])


def evaluate_k(X_scaled):
    rows = []
    rng = np.random.default_rng(RANDOM_STATE)
    n = len(X_scaled)
    for k in K_RANGE:
        base = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=N_INIT).fit(X_scaled)
        labels = base.labels_
        sizes = np.bincount(labels, minlength=k)
        seed_ari = [
            adjusted_rand_score(labels, KMeans(n_clusters=k, random_state=s, n_init=N_INIT).fit_predict(X_scaled))
            for s in SEEDS if s != RANDOM_STATE
        ]
        sub_ari = []
        for _ in range(N_SUBSAMPLES):
            idx = rng.choice(n, size=int(n * SUBSAMPLE_FRAC), replace=False)
            km = KMeans(n_clusters=k, random_state=RANDOM_STATE, n_init=N_INIT).fit(X_scaled[idx])
            sub_ari.append(adjusted_rand_score(labels, km.predict(X_scaled)))
        rows.append({
            "k": k,
            "silhouette": round(float(silhouette_score(X_scaled, labels)), 4),
            "inertia": round(float(base.inertia_), 1),
            "sizes": sizes.tolist(),
            "pcts": [round(s / n * 100, 2) for s in sizes],
            "min_pct": round(sizes.min() / n * 100, 2),
            "ari_seeds_min": round(float(min(seed_ari)), 4),
            "ari_seeds_mean": round(float(np.mean(seed_ari)), 4),
            "ari_subsample_min": round(float(min(sub_ari)), 4),
            "ari_subsample_mean": round(float(np.mean(sub_ari)), 4),
        })
    return rows


def print_evaluation(rows):
    print(f"{'k':>2} {'silhouette':>10} {'min_%':>6} {'ARI semillas (min/media)':>25} "
          f"{'ARI submuestras (min/media)':>28}  tamaños (%)")
    for r in rows:
        sizes = ", ".join(f"{s} ({p}%)" for s, p in zip(r["sizes"], r["pcts"]))
        print(f"{r['k']:>2} {r['silhouette']:>10.4f} {r['min_pct']:>6.2f} "
              f"{r['ari_seeds_min']:>12.4f} / {r['ari_seeds_mean']:<10.4f} "
              f"{r['ari_subsample_min']:>13.4f} / {r['ari_subsample_mean']:<12.4f}  {sizes}")


def main():
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--k", type=int, choices=list(K_RANGE), help="k final a entrenar y guardar")
    args = parser.parse_args()

    assert not set(FEATURES) & set(PRICE_COLUMNS), "Una variable de precio está en FEATURES"
    data_path = find_data_file(SOURCE_FILE)
    df = load_training_frame(data_path)
    print(f"Dataset: {data_path} ({len(df)} filas)")
    print(f"Features ({len(FEATURES)}): {FEATURES}")
    print(f"Nulos antes de imputar: {df[FEATURES].isna().sum()[lambda s: s > 0].to_dict()}")

    X_input = df[["distrito", "distrito_norm"] + FEATURES]
    space = Pipeline([("prep", ClusteringPreprocessor()), ("scaler", StandardScaler())]).fit(X_input)
    X_scaled = space.transform(X_input)
    rows = evaluate_k(X_scaled)
    print("\nEvaluación de k (K-Means sobre el espacio estandarizado, sin PCA):")
    print_evaluation(rows)

    if args.k is None:
        print("\nSolo evaluación: no se guardaron artefactos. Usar --k para entrenar el modelo final.")
        return

    k = args.k
    pipe = make_pipeline(k).fit(X_input)
    labels = pipe.named_steps["kmeans"].labels_
    assert np.array_equal(labels, pipe.predict(X_input)), "predict no reproduce las etiquetas de entrenamiento"
    sizes = np.bincount(labels, minlength=k)
    prep = pipe.named_steps["prep"]
    scaler = pipe.named_steps["scaler"]
    centroids = pd.DataFrame(scaler.inverse_transform(pipe.named_steps["kmeans"].cluster_centers_), columns=FEATURES)
    eval_k = next(r for r in rows if r["k"] == k)

    MODELS_DIR.mkdir(parents=True, exist_ok=True)
    joblib.dump(pipe, MODELS_DIR / PIPELINE_FILE)
    metadata = {
        "model": "RF1 perfil competitivo - K-Means sin variables de precio",
        "source": {
            "file": SOURCE_FILE,
            "path": data_path.resolve().relative_to(CODE_DIR.parents[2]).as_posix(),
            "sha256": sha256_of(data_path),
            "rows_in_file": int(len(df)),
            "canonical_notebook": "deliveries/week07/code/EDA_week07.ipynb",
        },
        "trained_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "n_observations": int(len(df)),
        "features": FEATURES,
        "excluded_features": EXCLUDED_FEATURES,
        "cleaning": {
            "rule": "valores fuera de rango -> NaN antes de imputar (mismo rango que valida la entrada)",
            "ranges": {k_: list(v) for k_, v in RANGES.items()},
            "values_set_to_nan": {c: int(n_) for c, n_ in df.attrs.get("out_of_range", {}).items()},
        },
        "imputation": {
            "antiguedad": "mediana por grupo distrital (distrito_norm de Week 7; <20 anuncios = 'Otros'); "
                          "fallback mediana global",
            "mantenimiento": "mediana por grupo distrital; fallback mediana global",
            "banos": "moda según dormitorios; fallback moda global (en inferencia banos es obligatorio)",
            "district_to_group": prep.district_to_group_,
            "group_medians": prep.group_medians_,
            "global_medians": prep.global_medians_,
            "banos_mode_by_dormitorios": {str(k_): v for k_, v in prep.banos_mode_by_dorm_.items()},
            "banos_global_mode": prep.banos_global_mode_,
        },
        "scaling": {
            "method": "StandardScaler ajustado en entrenamiento (incluye amenidades binarias, como en Week 7)",
            "mean": dict(zip(FEATURES, np.round(scaler.mean_, 6).tolist())),
            "scale": dict(zip(FEATURES, np.round(scaler.scale_, 6).tolist())),
        },
        "kmeans": {"n_init": N_INIT, "algorithm": "lloyd", "random_state": RANDOM_STATE},
        "random_state": RANDOM_STATE,
        "k_evaluated": list(K_RANGE),
        "k_evaluation": rows,
        "stability_method": f"ARI frente a random_state={RANDOM_STATE} con semillas {SEEDS}; "
                            f"ARI de {N_SUBSAMPLES} submuestras del {int(SUBSAMPLE_FRAC * 100)}% "
                            "(modelo ajustado en la submuestra y aplicado a todo el dataset)",
        "k_selected": k,
        "silhouette": eval_k["silhouette"],
        "cluster_sizes": {str(i): int(s) for i, s in enumerate(sizes)},
        "cluster_pcts": {str(i): round(s / len(df) * 100, 2) for i, s in enumerate(sizes)},
        "centroids_original_units": {str(i): centroids.loc[i].round(3).to_dict() for i in range(k)},
        "cluster_profiles": {str(c): p for c, p in build_cluster_profiles(df, labels).items()},
        "versions": {
            "python": platform.python_version(),
            "numpy": np.__version__,
            "pandas": pd.__version__,
            "scipy": scipy.__version__,
            "scikit-learn": sklearn.__version__,
            "joblib": joblib.__version__,
        },
    }
    (MODELS_DIR / METADATA_FILE).write_text(json.dumps(metadata, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"\nModelo k={k} guardado en {MODELS_DIR / PIPELINE_FILE}")
    print(f"Metadata en {MODELS_DIR / METADATA_FILE}")
    print("\nPerfiles (valores observados):")
    for cid, p in metadata["cluster_profiles"].items():
        top_amen = sorted(p["amenidades_pct"].items(), key=lambda kv: -kv[1])[:6]
        print(f"  cluster {cid}: n={p['n']} ({p['pct']}%) | área med {p['area_total']['mediana']} | "
              f"dorm med {p['dormitorios']['mediana']} | baños med {p['banos']['mediana']} | "
              f"antig med {p['antiguedad']['mediana']} | mant med {p['mantenimiento']['mediana']} | "
              f"amenidades top {top_amen}")


if __name__ == "__main__":
    main()
