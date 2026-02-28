import os
import time
import json
import asyncio
import requests
from dotenv import load_dotenv

from pageindex import PageIndexClient
import pageindex.utils as utils

from langchain_openai import AzureChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser


# Load ENV

load_dotenv()

PAGEINDEX_API_KEY = os.getenv("PAGEINDEX_API_KEY")

PDF_URL = r"D:\TCS_Work\pageindex_rag\fine tunig.pdf"
DOWNLOAD_DIR = "./data"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)


# Clients

pi_client = PageIndexClient(api_key=PAGEINDEX_API_KEY)

llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
    api_version=os.getenv("AZURE_OPENAI_API_VERSION"),
    temperature=0,
)

parser = StrOutputParser()


# Prompts


tree_search_prompt = ChatPromptTemplate.from_template("""
You are given a question and a tree structure of a document.

Question:
{query}

Document tree:
{tree}

Return JSON ONLY:

{{
 "thinking": "reason briefly",
 "node_list": ["node_id"]
}}
""")

answer_prompt = ChatPromptTemplate.from_template("""
Answer ONLY using the provided context.

Question:
{query}

Context:
{context}

Give concise grounded answer and mention node IDs used.
""")

tree_search_chain = tree_search_prompt | llm | parser
answer_chain = answer_prompt | llm | parser


print("#####################################")
print("tree_search_chain: ",tree_search_chain)
print("#####################################")
print("answer_chain: ",answer_chain)
print("#####################################")



# Async Main Flow


async def main():
    # Download PDF

    pdf_path = r"D:\TCS_Work\pageindex_rag\fine tunig.pdf"

    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"PDF not found at {pdf_path}")

    print("Using local PDF:", pdf_path)
    print("Submitting to PageIndex...")
    submit_resp = pi_client.submit_document(pdf_path)
    print("#####################################")
    print("submit res", submit_resp)
    doc_id = submit_resp.get("doc_id") or submit_resp

    print("Waiting for tree generation...")
    for _ in range(60):
        if pi_client.is_retrieval_ready(doc_id):
            print("pi client: ",pi_client)
            break
            
        time.sleep(5)
    else:
        raise RuntimeError("Tree generation timeout")

    # Fetch Tree
    tree_resp = pi_client.get_tree(doc_id, node_summary=True)
    print("tree response: ", tree_resp)
    tree = tree_resp.get("result", tree_resp)
    print("tree: ", tree)

    node_map = utils.create_node_mapping(tree)

    tree_without_text = utils.remove_fields(
        tree.copy(),
        fields=["text"]
    )

    query = "What are the conclusions in this document?"

    # Step 2: Reasoning Search

    print("LLM reasoning over tree...")

    tree_json = json.dumps(tree_without_text, indent=2)

    result_text = await tree_search_chain.ainvoke({
        "query": query,
        "tree": tree_json
    })

    result = json.loads(result_text)

    print("Selected nodes:", result["node_list"])
    # Step 3: Retrieve Nodes

    retrieved_texts = []

    for nid in result["node_list"]:
        node = node_map.get(nid)
        if not node:
            continue

        text = node.get("text", "")
        if isinstance(text, list):
            text = "\n\n".join(text)

        retrieved_texts.append(
            f"--- Node {nid}: {node.get('title')} ---\n{text}"
        )

    combined_context = "\n\n".join(retrieved_texts)


    # Step 4: Final Answer

    final_answer = await answer_chain.ainvoke({
        "query": query,
        "context": combined_context
    })

    print("\n===== FINAL ANSWER =====\n")
    print(final_answer)


if __name__ == "__main__":
    asyncio.run(main())