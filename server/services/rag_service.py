"""
RAG 核心服务：向量化入库与问答。
"""

from __future__ import annotations

import json
import os
from dataclasses import dataclass

from flask import current_app
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_chroma import Chroma
from langchain_community.chat_models import ChatOllama
from langchain_community.embeddings import OllamaEmbeddings
from langchain_core.messages import HumanMessage

from extensions import db
from models.chat_log import ChatLog
from models.document import DocChunk, Document
from models.document_status import DocumentStatus
from models.knowledge_base import KnowledgeBase
from services.file_loader import FileLoader
from services.utils import md5_text


@dataclass
class SourceItem:
    """回答来源条目。"""

    doc_id: int
    title: str
    chunk_index: int
    snippet: str
    score: float | None = None


class RagService:
    """
    RAG 服务类。
    """

    @staticmethod
    def clear_partial_ingest(doc_id: int, collection_name: str) -> None:
        """
        清理某文档已写入的切片与向量（用于重试入库或失败后回滚）。
        """

        chunks = DocChunk.query.filter_by(doc_id=doc_id).all()
        if chunks:
            ids = [f"doc:{doc_id}:chunk:{c.chunk_index}:{c.content_md5}" for c in chunks]
            vs = RagService._get_vector_store(collection_name)
            try:
                vs.delete(ids=ids)
            except Exception:
                pass
        DocChunk.query.filter_by(doc_id=doc_id).delete(synchronize_session=False)
        db.session.commit()

    @staticmethod
    def _get_vector_store(collection_name: str) -> Chroma:
        """
        按 collection 名获取 Chroma 实例（同一 persist 目录下多 collection）。
        """

        persist_dir = current_app.config["CHROMA_PERSIST_DIR"]
        os.makedirs(persist_dir, exist_ok=True)

        embeddings = OllamaEmbeddings(
            base_url=current_app.config["OLLAMA_BASE_URL"],
            model=current_app.config["OLLAMA_EMBED_MODEL"],
        )

        return Chroma(
            collection_name=collection_name,
            embedding_function=embeddings,
            persist_directory=persist_dir,
        )

    @staticmethod
    def ingest_document(doc_id: int, file_path: str, filename: str, title: str, collection_name: str) -> dict:
        """
        将单个文档解析、切分并写入 Chroma + MySQL。
        """

        RagService.clear_partial_ingest(doc_id=doc_id, collection_name=collection_name)

        file_type = FileLoader.detect_type(filename)
        text = FileLoader.load_text(file_path=file_path, file_type=file_type)
        text = (text or "").strip()
        if not text:
            raise ValueError("文档解析结果为空，请检查文件内容")

        cfg = current_app.config
        chunk_size = int(cfg.get("RAG_CHUNK_SIZE") or 1000)
        chunk_overlap = int(cfg.get("RAG_CHUNK_OVERLAP") or 150)
        splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
        chunks = splitter.split_text(text)
        if not chunks:
            raise ValueError("切分结果为空，请检查文本内容")

        vs = RagService._get_vector_store(collection_name)

        # 先写 MySQL（便于统计与审计），同时准备写入 Chroma 的 metadata
        metadatas: list[dict] = []
        ids: list[str] = []
        for idx, chunk in enumerate(chunks):
            content = chunk.strip()
            content_md5 = md5_text(content)

            db.session.add(
                DocChunk(
                    doc_id=doc_id,
                    chunk_index=idx,
                    content=content,
                    content_md5=content_md5,
                )
            )

            # Chroma 的 id 使用可复现字符串，便于后续删除/重建
            vector_id = f"doc:{doc_id}:chunk:{idx}:{content_md5}"
            ids.append(vector_id)
            metadatas.append(
                {
                    "doc_id": doc_id,
                    "title": title,
                    "chunk_index": idx,
                    "content_md5": content_md5,
                }
            )

        db.session.commit()

        # 写入向量库
        vs.add_texts(texts=[c.strip() for c in chunks], metadatas=metadatas, ids=ids)

        # 更新文档状态
        doc: Document | None = db.session.get(Document, doc_id)
        if doc:
            doc.status = DocumentStatus.INDEXED.value
            db.session.commit()

        return {"doc_id": doc_id, "chunks": len(chunks), "file_type": file_type}

    @staticmethod
    def build_rag_prompt_and_sources(question: str, knowledge_base_id: int) -> tuple[str, list[SourceItem]]:
        """
        向量检索并构造提示词；返回 (prompt, sources)。
        """

        kb: KnowledgeBase | None = db.session.get(KnowledgeBase, knowledge_base_id)
        if not kb:
            raise ValueError("知识库不存在")

        cfg = current_app.config
        top_k = max(1, min(50, int(cfg.get("RAG_TOP_K") or 5)))
        max_dist = cfg.get("RAG_MAX_DISTANCE")
        try:
            max_dist_f = float(max_dist) if max_dist is not None and str(max_dist).strip() != "" else None
        except (TypeError, ValueError):
            max_dist_f = None

        vs = RagService._get_vector_store(kb.collection_name)
        docs = vs.similarity_search_with_score(question, k=top_k)

        sources: list[SourceItem] = []
        context_parts: list[str] = []
        for doc, score in docs:
            if max_dist_f is not None and score is not None and float(score) > max_dist_f:
                continue
            meta = doc.metadata or {}
            doc_id = int(meta.get("doc_id") or 0)
            title = str(meta.get("title") or "")
            chunk_index = int(meta.get("chunk_index") or 0)
            snippet = (doc.page_content or "")[:200]
            sources.append(SourceItem(doc_id=doc_id, title=title, chunk_index=chunk_index, snippet=snippet, score=score))
            context_parts.append(f"【{title} | chunk#{chunk_index}】\n{doc.page_content}")

        context_text = "\n\n".join(context_parts).strip()
        if not context_text:
            context_text = "（知识库暂无命中内容）"

        extra = (cfg.get("RAG_PROMPT_EXTRA") or "").strip()
        extra_block = f"\n{extra}\n" if extra else ""

        prompt = f"""你是企业内部知识库问答助手，请基于给定的“知识库片段”回答用户问题。

要求：
1. 只根据知识库片段作答；如果片段不足以回答，请明确说明“知识库中没有找到相关信息”，并给出你需要的补充信息。
2. 回答用中文，条理清晰，必要时用列表。
3. 不要编造不存在的制度/流程/数字。{extra_block}
知识库片段：
{context_text}

用户问题：
{question}
"""
        return prompt, sources

    @staticmethod
    def stream_llm_answer_chunks(prompt: str):
        """
        流式输出模型回答文本片段（ChatOllama stream）。
        """

        temp = current_app.config.get("OLLAMA_TEMPERATURE")
        try:
            temperature = float(temp) if temp is not None else 0.2
        except (TypeError, ValueError):
            temperature = 0.2

        llm = ChatOllama(
            base_url=current_app.config["OLLAMA_BASE_URL"],
            model=current_app.config["OLLAMA_LLM_MODEL"],
            temperature=temperature,
        )
        messages = [HumanMessage(content=prompt)]
        try:
            for chunk in llm.stream(messages):
                piece = getattr(chunk, "text", None) or ""
                if piece:
                    yield piece
        except Exception:
            try:
                res = llm.invoke(messages)
                text = res.content if hasattr(res, "content") else str(res)
                if text:
                    yield text
            except Exception as e:
                raise RuntimeError(str(e) or "模型调用失败") from e

    @staticmethod
    def save_chat_log(user_id: int, question: str, answer: str, sources: list[SourceItem]) -> None:
        """写入问答日志。"""

        db.session.add(
            ChatLog(
                user_id=user_id,
                question=question,
                answer=answer,
                sources_json=json.dumps([s.__dict__ for s in sources], ensure_ascii=False, default=str),
            )
        )
        db.session.commit()

    @staticmethod
    def delete_document_embeddings(doc_id: int, collection_name: str) -> None:
        """
        从指定 Chroma collection 中移除该文档的全部向量（与入库时的 id 规则一致）。
        """

        RagService.clear_partial_ingest(doc_id=doc_id, collection_name=collection_name)

    @staticmethod
    def delete_chroma_collection(collection_name: str) -> None:
        """
        删除整个 Chroma collection（删除空知识库时使用）。
        """

        vs = RagService._get_vector_store(collection_name)
        try:
            vs.delete_collection()
        except Exception:
            pass

