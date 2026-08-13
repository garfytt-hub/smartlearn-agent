# ============================================================
# pdf_summary.py - PDF 结构化摘要工具
# ============================================================
# CLI 工具：读取 PDF 文件，通过 OpenRouter 调用 LLM，
# 输出包含 Overview、Key Points（附 [Page X] 引用）和 Limitations 三部分的结构化摘要。
# ============================================================

import os
import sys
import argparse
from openai import OpenAI
from dotenv import load_dotenv
import pymupdf  # PyMuPDF

# ---- 加载环境变量 ----
# 从 .env 文件中读取 OPENROUTER_API_KEY
load_dotenv()

# ---- 常量 ----
MODEL = "deepseek/deepseek-v4-flash-0731"
MAX_CHARS = 100_000  # 文本截断上限，避免超出上下文窗口


def extract_pages(pdf_path, page_start=None, page_end=None):
    """
    从 PDF 提取指定页面范围的文字。
    参数: pdf_path — PDF 文件路径
          page_start — 起始页码（从 1 开始，None 表示第 1 页）
          page_end — 结束页码（从 1 开始，None 或超出总页数时取最后一页）
    返回: [(page_num, text), ...] 列表，page_num 从 1 开始
    """
    try:
        doc = pymupdf.open(pdf_path)
    except FileNotFoundError:
        print(f"Error: File not found - '{pdf_path}'")
        sys.exit(1)
    except Exception as e:
        print(f"Error: Cannot open PDF - {e}")
        sys.exit(1)

    total_pages = doc.page_count
    if page_start is None:
        page_start = 1
    if page_end is None or page_end > total_pages:
        page_end = total_pages

    if page_start > total_pages:
        print(f"Error: START page ({page_start}) exceeds PDF total pages ({total_pages}).")
        doc.close()
        sys.exit(1)

    pages = []
    for page_num in range(page_start, page_end + 1):
        print(f"Extracting page {page_num}/{page_end}...")
        text = doc[page_num - 1].get_text().strip()  # pymupdf pages are 0-indexed; convert to 1-indexed
        pages.append((page_num, text))

    doc.close()
    return pages


def parse_page_range(range_str):
    """
    解析 --pages START-END 参数。
    参数: range_str — 如 "1-5" 的字符串
    返回: (start, end) 整数元组
    无效格式时打印友好提示并退出。
    """
    try:
        parts = range_str.split("-")
        if len(parts) != 2:
            raise ValueError("Range must be in START-END format (e.g., 1-5).")
        start = int(parts[0].strip())
        end = int(parts[1].strip())
    except (ValueError, AttributeError):
        print(f"Error: Invalid page range '{range_str}'. Expected format: START-END (e.g., 1-5).")
        print("Both START and END must be positive integers.")
        sys.exit(1)

    if start < 1 or end < 1:
        print(f"Error: Page numbers must be positive (got {start}-{end}).")
        sys.exit(1)
    if start > end:
        print(f"Error: START page ({start}) cannot be greater than END page ({end}).")
        sys.exit(1)

    return start, end


def has_extractable_text(pages):
    """检查 PDF 是否包含可提取的文字内容。"""
    total = "".join(text for _, text in pages).strip()
    return len(total) > 0


def build_prompt(pages):
    """
    将逐页文字组装为 prompt，每页加上 [Page N] 标记。
    如果文字超过 MAX_CHARS，截断并附加警告。
    """
    parts = []
    total_chars = 0
    truncated = False

    for page_num, text in pages:
        if not text:
            continue
        header = f"[Page {page_num}]\n"
        if total_chars + len(header) + len(text) > MAX_CHARS:
            # 截断到剩余可用字符数
            remaining = MAX_CHARS - total_chars - len(header)
            if remaining > 0:
                parts.append(header + text[:remaining])
            truncated = True
            break
        parts.append(header + text)
        total_chars += len(header) + len(text)

    numbered_text = "\n\n".join(parts)

    if truncated:
        numbered_text += (
            "\n\n[Note: PDF content too long; truncated. "
            + f"Summary based on first {len(parts)} pages only.]"
        )

    return numbered_text


def call_llm(prompt_text):
    """
    将文本发送给 LLM 并返回摘要。
    参数: prompt_text —带有 [Page N] 标记的 PDF 文字
    返回: LLM 生成的结构化摘要字符串
    """
    client = OpenAI(
        base_url="https://openrouter.ai/api/v1",
        api_key=os.getenv("OPENROUTER_API_KEY"),
    )

    system_prompt = (
        "You are a helpful assistant that summarizes PDF documents. "
        "Based on the provided text (which includes [Page X] markers), "
        "generate a structured summary with exactly these three sections:\n\n"
        "## Overview\n"
        "- A brief summary of what the document is about.\n\n"
        "## Key Points\n"
        "- List 3-5 main points from the document as numbered bullets (1, 2, 3, ...).\n"
        "- Every bullet MUST end with a [Page X] citation.\n\n"
        "## Limitations\n"
        "- Note any gaps, missing context, or limitations in the source text.\n\n"
        "Important: Only output these three sections. Do not add extra commentary."
    )

    user_prompt = (
        f"Here is the PDF content with page markers:\n\n{prompt_text}\n\n"
        "Please generate the structured summary with Overview, Key Points (with [Page X] citations), and Limitations."
    )

    try:
        response = client.chat.completions.create(
            model=MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.3,
        )
        return response.choices[0].message.content
    except Exception as e:
        print(f"Error: LLM call failed - {e}")
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(description="PDF Summary Tool")
    parser.add_argument("path", nargs="?", help="Path to the PDF file")
    parser.add_argument(
        "--pages", metavar="START-END",
        help="Page range to summarize (e.g., --pages 1-5)"
    )
    args = parser.parse_args()

    # ---- Check argument ----
    if args.path is None:
        print("Usage: python3 pdf_summary.py <path-to-pdf>")
        sys.exit(1)

    # ---- Parse page range (if provided) ----
    if args.pages is not None:
        page_start, page_end = parse_page_range(args.pages)
    else:
        page_start, page_end = None, None

    # ---- Extract PDF text (only the requested page range) ----
    pages = extract_pages(args.path, page_start, page_end)

    # ---- Check for extractable text ----
    if not has_extractable_text(pages):
        print("This PDF contains no extractable text (likely scanned).")
        print("Cannot generate a summary without text content.")
        sys.exit(0)

    # ---- Build prompt ----
    numbered_text = build_prompt(pages)

    # ---- Call LLM and print result ----
    print("Generating summary...\n")
    summary = call_llm(numbered_text)
    print(summary)


if __name__ == "__main__":
    main()
