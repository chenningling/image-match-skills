#!/usr/bin/env python3
"""
Extract image markers from a marked article and search Unsplash for matching photos.

Usage:
    python search_images.py <marked_md_path> <output_json_path>

Input:  Markdown file containing <!--IMAGE_N[keywords]--> markers
Output: JSON file with candidate photos for each marker
"""

import json
import os
import re
import sys
import time

try:
    import requests
except ImportError:
    print("错误: 需要 requests 库。请运行: pip install requests")
    sys.exit(1)

UNSPLASH_ACCESS_KEY = os.getenv("UNSPLASH_ACCESS_KEY")
API_URL = "https://api.unsplash.com/search/photos"
MAX_MARKERS = 10
CANDIDATES_PER_SEARCH = 5
REQUEST_DELAY = 0.5


def extract_markers(content: str) -> list:
    """Extract <!--IMAGE_N[keywords]--> markers from markdown."""
    pattern = r"<!--IMAGE_(\d+)\[(.+?)\]-->"
    markers = []
    for match in re.finditer(pattern, content):
        markers.append(
            {
                "id": int(match.group(1)),
                "keywords": match.group(2).strip(),
                "raw_marker": match.group(0),
            }
        )
    return markers


def search_unsplash(keywords: str, per_page: int = CANDIDATES_PER_SEARCH) -> dict:
    """Call Unsplash search API with landscape orientation."""
    if not UNSPLASH_ACCESS_KEY:
        raise RuntimeError(
            "未检测到环境变量 UNSPLASH_ACCESS_KEY。\n"
            "请先在终端中设置自己的 Unsplash API Access Key，例如：\n"
            "  export UNSPLASH_ACCESS_KEY=your_key_here"
        )
    resp = requests.get(
        API_URL,
        params={
            "query": keywords,
            "per_page": per_page,
            "orientation": "landscape",
            "content_filter": "high",
            "order_by": "relevant",
        },
        headers={"Authorization": f"Client-ID {UNSPLASH_ACCESS_KEY}"},
        timeout=15,
    )
    resp.raise_for_status()
    return resp.json()


def format_candidates(api_data: dict) -> list:
    """Extract relevant fields from each photo result."""
    candidates = []
    for photo in api_data.get("results", []):
        candidates.append(
            {
                "photo_id": photo["id"],
                "description": photo.get("description") or "",
                "alt_description": photo.get("alt_description") or "",
                "url_regular": photo["urls"]["regular"],
                "url_small": photo["urls"]["small"],
                "photographer": photo["user"]["name"],
                "photographer_url": photo["user"]["links"]["html"],
                "width": photo["width"],
                "height": photo["height"],
            }
        )
    return candidates


def main():
    if len(sys.argv) < 3:
        print("用法: python search_images.py <marked_md_path> <output_json_path>")
        sys.exit(1)

    md_path = sys.argv[1]
    output_path = sys.argv[2]

    with open(md_path, "r", encoding="utf-8") as f:
        content = f.read()

    markers = extract_markers(content)

    if not markers:
        print("未找到配图标记 <!--IMAGE_N[...]-->，请检查文件内容。")
        with open(output_path, "w", encoding="utf-8") as f:
            json.dump([], f)
        sys.exit(0)

    if len(markers) > MAX_MARKERS:
        print(
            f"⚠ 发现 {len(markers)} 个标记，超过上限 {MAX_MARKERS}，仅处理前 {MAX_MARKERS} 个。"
        )
        markers = markers[:MAX_MARKERS]

    print(f"发现 {len(markers)} 个配图标记，开始搜索 Unsplash...\n")

    results = []
    for i, marker in enumerate(markers):
        print(f"[{i + 1}/{len(markers)}] IMAGE_{marker['id']}: {marker['keywords']}")

        try:
            api_data = search_unsplash(marker["keywords"])
            candidates = format_candidates(api_data)
            total = api_data.get("total", 0)

            results.append(
                {
                    "image_id": marker["id"],
                    "keywords": marker["keywords"],
                    "raw_marker": marker["raw_marker"],
                    "total_found": total,
                    "candidates": candidates,
                }
            )
            print(f"  → 找到 {total} 张相关图片，返回 {len(candidates)} 个候选\n")

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response else "unknown"
            print(f"  → API 请求失败 (HTTP {status}): {e}\n")
            results.append(
                {
                    "image_id": marker["id"],
                    "keywords": marker["keywords"],
                    "raw_marker": marker["raw_marker"],
                    "total_found": 0,
                    "candidates": [],
                    "error": f"HTTP {status}: {str(e)}",
                }
            )

        except requests.exceptions.RequestException as e:
            print(f"  → 网络错误: {e}\n")
            results.append(
                {
                    "image_id": marker["id"],
                    "keywords": marker["keywords"],
                    "raw_marker": marker["raw_marker"],
                    "total_found": 0,
                    "candidates": [],
                    "error": str(e),
                }
            )

        if i < len(markers) - 1:
            time.sleep(REQUEST_DELAY)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    success_count = sum(1 for r in results if r["candidates"])
    print(f"搜索完成！{success_count}/{len(markers)} 个位置找到候选图片。")
    print(f"结果已保存到: {output_path}")


if __name__ == "__main__":
    main()
