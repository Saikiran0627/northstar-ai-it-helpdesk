"""Local TF-IDF retrieval over fictional IT support documents."""

from __future__ import annotations

import re
from pathlib import Path

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from northstar_helpdesk.models import KnowledgeChunk
from northstar_helpdesk.security import sanitize_document_text


TITLE_RE = re.compile(r"^#\s+(?P<title>.+)$", re.MULTILINE)


class KnowledgeBase:
    def __init__(self, knowledge_dir: Path):
        self.knowledge_dir = knowledge_dir
        self.documents = self._load_documents()
        if not self.documents:
            raise ValueError(f"No knowledge documents found in {knowledge_dir}")
        self.vectorizer = TfidfVectorizer(stop_words="english", ngram_range=(1, 2))
        self.matrix = self.vectorizer.fit_transform([doc.text for doc in self.documents])

    def _load_documents(self) -> list[KnowledgeChunk]:
        docs: list[KnowledgeChunk] = []
        for path in sorted(self.knowledge_dir.glob("*.md")):
            raw_text = path.read_text(encoding="utf-8")
            text = sanitize_document_text(raw_text)
            title_match = TITLE_RE.search(text)
            title = title_match.group("title") if title_match else path.stem.replace("-", " ").title()
            docs.append(
                KnowledgeChunk(
                    doc_id=path.stem,
                    title=title,
                    source=str(path.relative_to(self.knowledge_dir.parent.parent)),
                    text=text,
                )
            )
        return docs

    def search(self, query: str, limit: int = 3) -> list[KnowledgeChunk]:
        query_vector = self.vectorizer.transform([query])
        similarities = cosine_similarity(query_vector, self.matrix).ravel()
        ranked_indexes = similarities.argsort()[::-1][:limit]

        results: list[KnowledgeChunk] = []
        for index in ranked_indexes:
            score = float(similarities[index])
            if score <= 0:
                continue
            doc = self.documents[index]
            results.append(
                KnowledgeChunk(
                    doc_id=doc.doc_id,
                    title=doc.title,
                    source=doc.source,
                    text=doc.text,
                    score=score,
                )
            )
        return results
