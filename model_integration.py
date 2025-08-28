from dotenv import load_dotenv
from openai import OpenAI
from neo4j import GraphDatabase
from langgraph.graph import StateGraph, END
from typing import TypedDict, List, Dict, Any, Optional
#from galileo import galileo_context # The Galileo context manager
#from galileo.openai import openai as gal_openai
import json
import os
import re

load_dotenv()


class GraphState(TypedDict, total=False):
    """State that flows through the LangGraph.

    Keys:
    - question: The user's natural-language question.
    - schema: A lightweight textual summary of the graph schema (best-effort).
    - cypher: The Cypher query generated for the question.
    - rows: Query results as a list of dictionaries.
    - answer: Final natural-language answer for the user.
    """

    question: str
    schema: str
    cypher: str
    rows: List[Dict[str, Any]]
    answer: str


def _create_client() -> OpenAI:
    sn_client = OpenAI(base_url="https://api.sambanova.ai/v1/",
        api_key=os.environ.get("SAMBANOVA_API_KEY"))

    # model = "DeepSeek-R1-Distill-Llama-70B"
    # prompt = "Tell me a joke about artificial intelligence."

    # completion = sn_client.chat.completions.create(
    #     model=model,
    #     messages=[
    #         {
    #             "role": "user", 
    #             "content": prompt,
    #         }
    #     ],
    #     stream=True,
    # )

    # response = ""
    # for chunk in completion:
    #     if (token := chunk.choices[0].delta.content):
    #         print(token, flush=True, end="")
    
    return sn_client


def _get_neo4j_driver():
    uri = os.environ.get("NEO4J_URI")
    user = os.environ.get("NEO4J_USERNAME")
    password = os.environ.get("NEO4J_PASSWORD")
    if not uri or not user or not password:
        raise RuntimeError(
            "NEO4J_URI, NEO4J_USERNAME, and NEO4J_PASSWORD must be set in the environment."
        )
    return GraphDatabase.driver(uri, auth=(user, password))


def _introspect_schema_text() -> str:
    """Return a small textual summary of the Neo4j schema (best-effort)."""
    try:
        driver = _get_neo4j_driver()
    except Exception:
        return ""

    try:
        with driver.session() as session:
            try:
                record = session.run("CALL db.schema.visualization()").single()
                if record is None:
                    return ""
                nodes = record.get("nodes", [])
                relationships = record.get("relationships", [])
                label_set = sorted({(n.get("labels") or ["?"])[0] for n in nodes})
                rel_type_set = sorted({r.get("type", "?") for r in relationships})
                return (
                    f"Node labels: {', '.join(label_set)}; "
                    f"Relationship types: {', '.join(rel_type_set)}"
                )
            except Exception:
                # Fallback when visualization proc isn't available.
                node_rows = session.run("CALL db.labels()").data()
                rel_rows = []
                try:
                    rel_rows = session.run("CALL db.relationshipTypes()").data()
                except Exception:
                    try:
                        # Neo4j 5 alternative
                        rel_rows = session.run("SHOW RELATIONSHIP TYPES").data()
                    except Exception:
                        rel_rows = []
                labels = sorted({row.get("label", "?") for row in node_rows})
                rel_types = sorted({
                    row.get("relationshipType") or row.get("name") or row.get("type", "?")
                    for row in rel_rows
                })
                if rel_types:
                    return (
                        f"Node labels: {', '.join(labels)}; "
                        f"Relationship types: {', '.join(rel_types)}"
                    )
                return f"Node labels: {', '.join(labels)}"
    except Exception:
        return ""
    finally:
        try:
            driver.close()
        except Exception:
            pass


def _extract_cypher_from_text(text: str) -> str:
    """Extract a Cypher statement from LLM output.

    Handles reasoning tags (e.g., <think>...</think>), markdown fences, and headings.
    Prefers ```cypher fenced blocks, then any fenced block, then heuristic line scan.
    """
    if not text:
        return ""

    # Remove chain-of-thought/reasoning tags if present
    cleaned = re.sub(r"<think>[\s\S]*?</think>", "", text, flags=re.IGNORECASE)

    # Prefer an explicit cypher code fence
    match = re.search(r"```\s*[Cc]ypher\s+([\s\S]*?)```", cleaned)
    if not match:
        # Fallback: any fenced block
        match = re.search(r"```\s*([\s\S]*?)```", cleaned)
    if match:
        candidate = match.group(1).strip()
    else:
        # Remove bold markers and obvious headings
        reduced = cleaned.replace("**", "")
        reduced = re.sub(r"(?i)^\s*cypher\s+query\s*:\s*", "", reduced)
        # Heuristic: find first line that looks like Cypher and take until blank line
        lines = [ln.strip() for ln in reduced.splitlines()]
        start_idx: Optional[int] = None
        for idx, ln in enumerate(lines):
            if re.match(r"^(MATCH|CALL|WITH|UNWIND|RETURN|CREATE|MERGE|OPTIONAL|USE)\b", ln, re.IGNORECASE):
                start_idx = idx
                break
        if start_idx is not None:
            # Collect contiguous non-empty lines after start
            collected: List[str] = []
            for ln in lines[start_idx:]:
                if not ln:
                    break
                collected.append(ln)
            candidate = "\n".join(collected).strip()
        else:
            candidate = cleaned.strip()

    # Final cleanup: strip stray fences, quotes, and trailing markdown artifacts
    candidate = candidate.strip().strip("`").strip()
    candidate = re.sub(r"^`+|`+$", "", candidate)
    candidate = re.sub(r"^[\"']+|[\"']+$", "", candidate)
    return candidate


def _generate_cypher_from_question(question: str, schema_text: str, model: Optional[str] = None) -> str:
    client = _create_client()
    selected_model = model or os.environ.get("MODEL_FAST", "Meta-Llama-3.3-70B-Instruct")
    system_prompt = (
        "You are an expert in Neo4j Cypher. "
        "Use ONLY the node labels and relationship types explicitly listed in the provided schema. "
        "Do not invent labels or relationship types. If a label is not listed, do not use it. "
        "Return ONLY a single valid Cypher query. No commentary. No markdown fences."
    )
    user_prompt = (
        f"Schema: {schema_text or 'Unknown'}\n\n"
        f"Question: {question}"
    )
    completion = client.chat.completions.create(
        model=selected_model,
        temperature=0,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    )
    raw = (completion.choices[0].message.content or "").strip()
    cypher = _extract_cypher_from_text(raw)
    return cypher


def _run_cypher(cypher: str) -> List[Dict[str, Any]]:
    driver = _get_neo4j_driver()
    with driver.session() as session:
        result = session.run(cypher)
        rows: List[Dict[str, Any]] = [record.data() for record in result]
    driver.close()
    return rows


def _query_db_node(state: GraphState) -> GraphState:
    question = state.get("question", "").strip()
    if not question:
        raise ValueError("question is required in the state")

    schema_text = _introspect_schema_text()
    cypher = _generate_cypher_from_question(question=question, schema_text=schema_text)

    try:
        rows = _run_cypher(cypher)
    except Exception as exc:
        rows = []
        rows.append({"error": str(exc)})

    return {"schema": schema_text, "cypher": cypher, "rows": rows}


def _reply_node(state: GraphState) -> GraphState:
    client = _create_client()
    selected_model = os.environ.get("MODEL", "Deepseek-V3.1")
    question = state.get("question", "")
    rows = state.get("rows", [])

    assistant_instructions = (
        "You answer the user's question using ONLY the provided Neo4j query results. "
        "If the results are empty, explain that you don't have hard data in the database and provide result to the best of your knowledge. "
        "Don't say that you don't have enough data and cannot confirm anything, just answer to the best of your ability and comment that you could refine your answer given more data. "
        "Be concise and precise. If there was an execution error, surface it succinctly and politely."
    )
    user_content = (
        f"Question: {question}\n\n" +
        f"Data (JSON):\n{json.dumps(rows, ensure_ascii=False, indent=2)}"
    )

    completion = client.chat.completions.create(
        model=selected_model,
        temperature=0.2,
        messages=[
            {"role": "system", "content": assistant_instructions},
            {"role": "user", "content": user_content},
        ],
    )
    answer = (completion.choices[0].message.content or "").strip()
    return {"answer": answer}


def set_up_agents():
    """Create and compile the LangGraph with QueryDB and Reply nodes."""
    graph = StateGraph(GraphState)
    graph.add_node("query_db", _query_db_node)
    graph.add_node("reply", _reply_node)
    graph.set_entry_point("query_db")
    graph.add_edge("query_db", "reply")
    graph.add_edge("reply", END)
    return graph.compile()


def agent_querydb(question: str) -> str:
    """Run the compiled graph end-to-end and return the final answer string."""
    app = set_up_agents()
    final_state = app.invoke({"question": question})
    return final_state.get("answer", "")

graph = set_up_agents()
def generate_text(input: str) -> str:
    result = graph.invoke({"question": input})

    answer = result.get("answer", "")
    # Remove <think>...</think> tags and any content inside, if present
    answer = re.sub(r"<think>.*?</think>\s*", "", answer, flags=re.DOTALL)
    # If the answer is wrapped in a dict, extract the 'answer' field
    result["answer"] = answer.strip()

    return result["answer"]

if __name__ == "__main__":
    print(generate_text("Who were the actors in The Matrix?"))