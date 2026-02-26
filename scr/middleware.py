"""Agent middleware for post-processing tool results."""
import asyncio
from typing import Callable
from langchain.messages import ToolMessage
from langchain.agents.middleware import wrap_tool_call
from langchain.tools.tool_node import ToolCallRequest
from langgraph.types import Command
from langchain_openai import ChatOpenAI

from scr.config import settings
from scr.logger import setup_logger

logger = setup_logger(__name__)

CHUNK_SIZE = 10_000
OVERLAP = 500  # символов в каждую сторону → оверлап-чанк = 1 000 символов


def _build_chunks(text: str) -> list[str]:
    """Разбивает текст на основные чанки по CHUNK_SIZE символов.

    На каждой внутренней границе добавляется один оверлап-чанк
    размером OVERLAP*2 (OVERLAP символов влево + OVERLAP символов вправо).
    """
    chunks: list[str] = []
    length = len(text)

    if length == 0:
        return chunks

    # Границы основных чанков
    boundaries = list(range(0, length, CHUNK_SIZE))

    for i, start in enumerate(boundaries):
        end = min(start + CHUNK_SIZE, length)
        chunks.append(text[start:end])

        # Добавляем оверлап-чанк после каждого основного чанка, кроме последнего
        boundary = end  # правая граница текущего основного чанка
        if boundary < length:
            ol_start = max(0, boundary - OVERLAP)
            ol_end = min(length, boundary + OVERLAP)
            chunks.append(text[ol_start:ol_end])

    return chunks


def _make_prompt(chunk: str, query: str) -> str:
    return (
        f"You are a meticulous information extractor. Carefully read the following source text:\n\n"
        f"<source_text>\n{chunk}\n</source_text>\n\n"
        f"Based ONLY on the <source_text> above, your task is to extract ALL information related to the following query:\n"
        f"<query>\n{query}\n</query>\n\n"
        f"Extraction Rules:\n"
        f"1. Search the text specifically for terms and concepts related to the <query>.\n"
        f"2. Extract facts, descriptions, context, and methodology strictly related to the <query>.\n"
        f"3. Do NOT summarize the whole text. Focus ONLY on parts relevant to the <query>.\n"
        f"4. Present the findings as a detailed bulleted list.\n"
        f"5. If the <source_text> does not contain any information related to the <query>, "
        f"reply exactly with: 'No relevant information found.'"
    )


NO_INFO = "No relevant information found."


@wrap_tool_call
async def extract_facts_middleware(
    request: ToolCallRequest,
    handler: Callable[[ToolCallRequest], ToolMessage | Command],
) -> ToolMessage | Command:
    """Middleware that post-processes search_documents results.

    Splits the raw result into chunks of CHUNK_SIZE characters plus
    overlap chunks of OVERLAP*2 characters at every boundary, queries a
    cheap LLM for each chunk in parallel, then concatenates the non-empty
    findings into a single string.

    For all other tools the result is returned unchanged.
    """
    result = await handler(request)

    if request.tool_call["name"] != "search_documents":
        return result

    query = request.tool_call["args"].get("query", "")

    # 1. Достаем сырой контент
    raw_content = result.content if isinstance(result, ToolMessage) else str(result)

    # 2. Распаковываем список блоков LangChain обратно в строку
    if isinstance(raw_content, list):
        texts = [
            block.get("text", "")
            for block in raw_content
            if isinstance(block, dict) and block.get("type") == "text"
        ]
        clean_text = "\n".join(texts)
    else:
        clean_text = str(raw_content)

    # 3. Исправляем экранированные переносы строк
    clean_text = clean_text.replace("\\n", "\n")

    logger.info(
        "extract_facts_middleware",
        extra={
            "tool": "search_documents",
            "query": query,
            "raw_length": len(clean_text),
        },
    )

    extractor_llm = ChatOpenAI(
        model=settings.extractor_model,
        api_key=settings.openrouter_api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.2,
    )

    # 4. Разбиваем текст на чанки + оверлапы
    chunks = _build_chunks(clean_text)

    logger.info(
        "extract_facts_middleware_chunks",
        extra={"num_chunks": len(chunks)},
    )

    # 5. Параллельно запрашиваем LLM для каждого чанка
    async def extract_chunk(chunk: str) -> str:
        try:
            prompt = _make_prompt(chunk, query)
            response = await extractor_llm.ainvoke(prompt)
            return response.content
        except Exception as e:
            logger.error("extract_facts_middleware_chunk_error", extra={"error": str(e)})
            return ""

    try:
        results = await asyncio.gather(*[extract_chunk(c) for c in chunks])

        # 6. Оставляем только непустые и содержательные ответы
        meaningful = [
            r for r in results
            if r.strip() and r.strip() != NO_INFO
        ]

        extracted = "\n".join(meaningful) if meaningful else NO_INFO

        logger.info(
            "extract_facts_middleware_done",
            extra={
                "query": query,
                "chunks_total": len(chunks),
                "chunks_with_info": len(meaningful),
                "extracted_length": len(extracted),
            },
        )

        return ToolMessage(
            content=extracted,
            tool_call_id=result.tool_call_id,
        )
    except Exception as e:
        # On failure — return the original result so the agent still works
        logger.error("extract_facts_middleware_error", extra={"error": str(e)})
        return result
