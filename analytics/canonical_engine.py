# ==========================================================
# ADVANCED CANONICAL CLUSTERING ENGINE (Agglomerative)
# ==========================================================

import json
import numpy as np
from pathlib import Path
from collections import defaultdict
from sklearn.cluster import AgglomerativeClustering
from sklearn.metrics import pairwise_distances

from .embedding_engine import EmbeddingEngine

# 0.75 Similarity means maximum 0.25 Distance
SIMILARITY_THRESHOLD = 0.45
DISTANCE_THRESHOLD = 1.0 - SIMILARITY_THRESHOLD

def find_medoid(cluster_indices, embeddings):
    """
    Finds the most representative question in a cluster (the center).
    """
    cluster_embeddings = [embeddings[i] for i in cluster_indices]
    
    # Calculate how similar each question is to every other question in the cluster
    dist_matrix = pairwise_distances(cluster_embeddings, metric="cosine")
    
    # The medoid is the one with the smallest total distance to all others
    sum_distances = dist_matrix.sum(axis=1)
    medoid_idx_relative = np.argmin(sum_distances)
    
    return cluster_indices[medoid_idx_relative]

def cluster_questions_within_topic(question_entries, embedding_engine):
    """
    Uses Agglomerative Clustering to group questions.
    """
    texts = [q["text"] for q in question_entries]
    
    # Flattening to ensure shape is (n_samples, n_features)
    embeddings = np.array(embedding_engine.encode(texts))
    if len(embeddings.shape) > 2:
        embeddings = embeddings.reshape(embeddings.shape[0], -1)

    # If only 1 question, return it as a single cluster
    if len(question_entries) < 2:
        return [[0]], embeddings

    # Compute pairwise cosine distances
    dist_matrix = pairwise_distances(embeddings, metric="cosine")

    # Perform clustering
    # 'average' linkage ensures all members of the cluster are relatively close
    clustering_model = AgglomerativeClustering(
        n_clusters=None,
        metric="precomputed",
        linkage="average",
        distance_threshold=DISTANCE_THRESHOLD
    )
    
    labels = clustering_model.fit_predict(dist_matrix)

    # Group original indices by their new cluster labels
    clustered_groups = defaultdict(list)
    for idx, label in enumerate(labels):
        clustered_groups[label].append(idx)

    return list(clustered_groups.values()), embeddings

def compute_canonical_questions(mapped_results, course_code, output_dir):
    embedding_engine = EmbeddingEngine()
    topic_questions = defaultdict(list)

    # 1. Organize questions by topic
    for q in mapped_results:
        for t in q.get("mapped_topics", []):
            topic = t["topic"]
            if topic == "Module-Level Fallback":
                continue

            topic_questions[topic].append({
                "paper_name": q["paper_name"],
                "question_number": q["question_number"],
                "text": q["text"]
            })

    print(f"\n🔍 Analyzing {len(topic_questions)} distinct topics for canonical patterns...")
    canonical_output = {}
    total_clusters = 0

    # 2. Cluster per topic
    for topic, questions in topic_questions.items():
        if len(questions) < 2:
            continue

        clusters, embeddings = cluster_questions_within_topic(questions, embedding_engine)
        canonical_groups = []

        for cluster_indices in clusters:
            if len(cluster_indices) < 2:
                continue  # Ignore questions that have no matches

            # Find the best representative question
            medoid_idx = find_medoid(cluster_indices, embeddings)
            representative = questions[medoid_idx]["text"]

            references = [
                f"{questions[i]['paper_name']} - {questions[i]['question_number']}"
                for i in cluster_indices
            ]

            canonical_groups.append({
                "canonical_question": representative,
                "occurrences": len(cluster_indices),
                "references": sorted(references) # Sorted for clean reading
            })

        if canonical_groups:
            canonical_groups.sort(key=lambda x: x["occurrences"], reverse=True)
            canonical_output[topic] = canonical_groups
            total_clusters += len(canonical_groups)

    print(f"📊 Formed {total_clusters} Canonical Clusters across {len(canonical_output)} topics.")

    # 3. Save output
    output_dir.mkdir(parents=True, exist_ok=True)
    file_path = output_dir / f"canonical_questions_{course_code}.json"

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(canonical_output, f, indent=4)

    print(f"📚 Saved to: {file_path}")
    return canonical_output