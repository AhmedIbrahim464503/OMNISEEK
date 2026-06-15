import os
import json
import urllib.request
from typing import Any, Dict, List
from core.logging import logger

class ResponseSynthesisService:
    """Service to synthesize a structured, cohesive response to a search query based on retrieved snippets."""

    @staticmethod
    def synthesize_response(query: str, results: List[Dict[str, Any]]) -> str:
        """
        Synthesizes a response by querying Gemini/OpenAI if API keys are available.
        Otherwise, falls back to a clean, structured local summary of matches.
        """
        if not results:
            return "No matching source segments were retrieved to synthesize an answer."

        # Read keys
        gemini_key = os.getenv("GEMINI_API_KEY")
        openai_key = os.getenv("OPENAI_API_KEY")

        # Compile search context for prompt
        context_parts = []
        for idx, r in enumerate(results):
            modality = r.get("modality", "TEXT")
            asset_name = r.get("asset_name", "Unknown Document")
            content = r.get("content", "")
            
            # Format time marker if available
            time_marker = ""
            if r.get("start_time") is not None:
                start_m = int(r["start_time"] // 60)
                start_s = int(r["start_time"] % 60)
                time_marker = f" (at {start_m:02d}:{start_s:02d})"

            context_parts.append(
                f"[{idx + 1}] Source: {asset_name} | Modality: {modality}{time_marker}\n"
                f"Content: \"{content}\"\n"
            )
        
        context_text = "\n".join(context_parts)

        # Call Gemini if available
        if gemini_key:
            logger.info("Synthesizing response using Google Gemini API...")
            try:
                prompt = (
                    "You are OMNISEEK, an advanced search assistant. Synthesize a unified, structured, "
                    "and clean response to the user's search query based ONLY on the provided context matches.\n"
                    "Use professional Markdown formatting, add bold key concepts, list key takeaways in bullet points, "
                    "and reference source documents using their bracketed citation numbers (e.g. [1], [2]).\n"
                    "Keep the answer relevant to the query and avoid mentioning that you are reading context. "
                    "If the context cannot answer the query, state that clearly.\n\n"
                    f"User Search Query: \"{query}\"\n\n"
                    f"Context Matches:\n{context_text}\n"
                )
                
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={gemini_key}"
                data = {
                    "contents": [{
                        "parts": [{
                            "text": prompt
                        }]
                    }]
                }
                
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode("utf-8"),
                    headers={"Content-Type": "application/json"}
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    resp_data = json.loads(response.read().decode("utf-8"))
                    summary = resp_data["candidates"][0]["content"]["parts"][0]["text"]
                    return summary.strip()
            except Exception as e:
                logger.error(f"Gemini API synthesis call failed: {e}. Falling back...")

        # Call OpenAI if available
        if openai_key:
            logger.info("Synthesizing response using OpenAI API...")
            try:
                prompt = (
                    "Synthesize a unified, structured response to the user's search query based ONLY on the provided context matches.\n"
                    "Use professional Markdown formatting, bold key concepts, bullet lists, "
                    "and cite the source documents (e.g. [1], [2]). "
                    "If the context cannot answer the query, state that clearly.\n\n"
                    f"User Search Query: \"{query}\"\n\n"
                    f"Context Matches:\n{context_text}\n"
                )
                
                url = "https://api.openai.com/v1/chat/completions"
                data = {
                    "model": "gpt-4o-mini",
                    "messages": [
                        {"role": "system", "content": "You are OMNISEEK, a professional search assistant."},
                        {"role": "user", "content": prompt}
                    ],
                    "temperature": 0.3
                }
                
                req = urllib.request.Request(
                    url,
                    data=json.dumps(data).encode("utf-8"),
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {openai_key}"
                    }
                )
                with urllib.request.urlopen(req, timeout=10) as response:
                    resp_data = json.loads(response.read().decode("utf-8"))
                    summary = resp_data["choices"][0]["message"]["content"]
                    return summary.strip()
            except Exception as e:
                logger.error(f"OpenAI API synthesis call failed: {e}. Falling back...")

        # Fallback to local rule-based synthesis
        logger.info("Synthesizing response using local rule-based fallback summary...")
        
        # Group contents by asset name
        grouped_results: Dict[str, List[Dict[str, Any]]] = {}
        for r in results:
            asset_name = r.get("asset_name", "Unknown Asset")
            if asset_name not in grouped_results:
                grouped_results[asset_name] = []
            grouped_results[asset_name].append(r)
        
        fallback_markdown = [
            f"### 🔍 Local Synthesis Summary for: \"{query}\"\n",
            "*(No cloud LLM API key configured in `.env`. Falling back to local structured synthesis.)*\n",
            "**Key Findings & Matches:**\n"
        ]

        for asset_name, chunks in grouped_results.items():
            fallback_markdown.append(f"- **From source: `{asset_name}`**")
            for c in chunks:
                time_str = ""
                if c.get("start_time") is not None:
                    start_m = int(c["start_time"] // 60)
                    start_s = int(c["start_time"] % 60)
                    time_str = f" [at {start_m:02d}:{start_s:02d}]"
                
                match_type = c.get("explanation", {}).get("match_type", "Vector Match")
                score_pct = int(c.get("score", 0.0) * 100)
                
                content_snippet = c.get("content", "").strip()
                if len(content_snippet) > 200:
                    content_snippet = content_snippet[:200] + "..."

                fallback_markdown.append(
                    f"  - *({match_type} - {score_pct}% match){time_str}:* \"{content_snippet}\""
                )
        
        return "\n".join(fallback_markdown)
