"""Reciprocal Rank Fusion (RRF) 融合函数"""

from typing import Any


def rrf_fuse(
    ranked_lists: list[list[tuple[str, dict[str, Any]]]],
    k_constant: int = 60,
    top_k: int = 10,
) -> tuple[list[str], list[dict[str, Any]]]:
    """对多条排序结果列表进行倒数排名融合 (RRF)。

    RRF 公式: score(d) += 1 / (k_constant + rank)

    按 (source, chunk_index) 去重：同一子查询内重复的不重复计分。

    Args:
        ranked_lists: 多条排序结果列表，每条为 (doc_id, metadata) 元组列表。
        k_constant: RRF 常数，默认 60。
        top_k: 返回结果数量，默认 10。

    Returns:
        (doc_ids, metadatas) 的元组，按 RRF 得分降序排列。
    """
    if not ranked_lists:
        return [], []

    # 只有一条列表：原样返回（截断到 top_k）
    if len(ranked_lists) == 1:
        items = ranked_lists[0][:top_k]
        return [item[0] for item in items], [item[1] for item in items]

    # 多条列表：RRF 融合
    # key = (source, chunk_index) → score
    score_map: dict[tuple[str, int], float] = {}
    # key → (doc_id, metadata)，取首次出现的 metadata
    doc_map: dict[tuple[str, int], tuple[str, dict[str, Any]]] = {}

    for ranked_list in ranked_lists:
        seen_in_list: set[tuple[str, int]] = set()
        for rank, (doc_id, meta) in enumerate(ranked_list, start=1):
            src = meta.get("source", "") if meta else ""
            ci = meta.get("chunk_index", -1) if meta else -1
            key = (src, ci)

            # 同一子查询内去重
            if key in seen_in_list:
                continue
            seen_in_list.add(key)

            # 累计 RRF 分数
            score_map[key] = score_map.get(key, 0.0) + 1.0 / (k_constant + rank)

            # 保留首次出现的 doc_id 和 metadata
            if key not in doc_map:
                doc_map[key] = (doc_id, meta)

    if not score_map:
        return [], []

    # 按分数降序排列，取 top_k
    sorted_keys = sorted(score_map.keys(), key=lambda k: score_map[k], reverse=True)
    sorted_keys = sorted_keys[:top_k]

    docs = [doc_map[k][0] for k in sorted_keys]
    metas = [doc_map[k][1] for k in sorted_keys]

    return docs, metas
