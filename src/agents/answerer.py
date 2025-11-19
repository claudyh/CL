from typing import List

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_ollama import ChatOllama
from langchain_community.vectorstores import InMemoryVectorStore

from src.common.models import QueryPlan, RowData
from src.rag.retriever import retrieve_with_rag


ANSWER_SYSTEM_PROMPT = SystemMessage(
  "You answer questions about historical facts involving Portugal using ONLY the context provided.\n\n"
  "The context contains rows derived from CSV files. Each row describes a tenure, with:\n"
  "- subject: the person (e.g. 'Manuel I of Portugal')\n"
  "- predicate: typically 'heldPosition'\n"
  "- object: the role (e.g. 'Monarch of Portugal')\n"
  "- start_date: the start date of the tenure\n"
  "- end_date: the end date of the tenure\n\n"
  "Very important rules:\n"
  "1. A tenure MATCHES a question about a specific year Y if Y is between start_date and end_date (inclusive).\n"
  "2. A tenure MATCHES a question about a range of years [A, B] if its period overlaps that range.\n"
  "3. You ARE allowed to do simple date reasoning (checking if a year falls between two years).\n"
  "4. You MUST NOT invent people, dates, or roles that are not present in the context.\n"
  "5. When you answer, you MUST output one CSV line per matching tenure, using EXACTLY this format:\n"
  "   subject,predicate,object,start_date,end_date\n"
  "   If multiple tenures match, output multiple lines, one per line.\n"
  "6. If no tenures match the question based on the context, answer with exactly:\n"
  "   NOT_SURE\n"
)


answer_llm = ChatOllama(model="llama3.1:8b")


def answer_with_rag(plan: QueryPlan, question: str, vector_store: InMemoryVectorStore) -> str:
  docs = retrieve_with_rag(plan, vector_store)

  if not docs:
    context = "NO_RELEVANT_CONTEXT"
  else:
    context_parts = []
    for i, d in enumerate(docs):
      context_parts.append(
        f"--- Document {i+1} ---\n"
        f"Source type: {d.metadata.get('source_type')}\n"
        f"Subject: {d.metadata.get('subject')}\n"
        f"Predicate: {d.metadata.get('predicate')}\n"
        f"Object: {d.metadata.get('object')}\n"
        f"Start date: {d.metadata.get('start_date')}\n"
        f"End date: {d.metadata.get('end_date')}\n\n"
        f"{d.page_content}"
      )
    context = "\n\n".join(context_parts)

  messages = [
    ANSWER_SYSTEM_PROMPT,
    HumanMessage(
      content=(
        f"Question: {question}\n\n"
        f"Structured plan (you may use it, but it might contain mistakes): {plan.model_dump()}\n\n"
        f"Context (rows from the CSV-derived documents):\n{context}\n\n"
        "From this context, identify all tenures that match the question "
        "according to the rules. Remember to output either one or more CSV lines "
        "in the exact format 'subject,predicate,object,start_date,end_date', or "
        "NOT_SURE if nothing matches."
      )
    ),
  ]

  response = answer_llm.invoke(messages)
  return response.content


LIGHTER_SYSTEM_PROMPT = SystemMessage(
  "You answer questions about historical facts involving Portugal using ONLY the context provided.\n\n"
  "The context contains rows derived from CSV files. Each row describes a tenure, with:\n"
  "- subject\n"
  "- predicate\n"
  "- object\n"
  "- start_date\n"
  "- end_date\n\n"
  "When you answer, you MUST output a pretty-printed answer based on the data and question provided.\n"
  "If the data is insufficient to answer the question, simply say that you do not know.\n"
)


def answer(question: str, data: List[RowData]) -> str:
  """Call the LLM to answer based on provided data rows."""

  print(data)

  messages = [
    LIGHTER_SYSTEM_PROMPT,
    HumanMessage(
      content=(
        f"Question: {question}\n\n"
        f"Data rows:\n" +
        ("\n".join(
          f"- {row.subject}, {row.predicate}, {row.object}, {row.start_date}, {row.end_date}"
          for row in data
        ) if data else "NO_RELEVANT_DATA") +
        "\n\nBased on the data, provide a concise answer to the question."
      )
    ),
  ]

  response = answer_llm.invoke(messages)
  return response.content
