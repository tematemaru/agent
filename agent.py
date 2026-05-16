import os
import json
from typing import Dict, Any, List

from ollama import chat

from tools import (
    write_file,
    read_file,
    list_files,
    run_shell
)

from loaders import load_file

# ===== RAG =====

from langchain_text_splitters import RecursiveCharacterTextSplitter

from langchain_ollama import OllamaEmbeddings

from langchain_chroma import Chroma

# =========================
# CONFIG
# =========================

MODEL_NAME = "qwen3:4b"

EMBED_MODEL = "nomic-embed-text"

DOCS_PATH = "./workspace/docs"

DB_PATH = "./chroma_db"

WORKSPACE = "./workspace"

MAX_HISTORY = 20

MAX_STEPS = 5

CHUNK_SIZE = 1200

CHUNK_OVERLAP = 200


# =========================
# SYSTEM PROMPT
# =========================

SYSTEM_PROMPT = """
Ты — AI агент, который работает с файловой системой через инструменты.

ТЫ НЕ МОЖЕШЬ напрямую читать или писать файлы.
Ты ОБЯЗАН использовать tools.

=========================
ФОРМАТ ОТВЕТА
=========================

Только JSON:

1) вызов инструмента:
{
  "type": "tool",
  "name": "tool_name",
  "args": { ... }
}

2) финальный ответ:
{
  "type": "final",
  "text": "..."
}

=========================
TOOLS
=========================

read_file:
{
  "path": "doc://test.txt"
}

write_file:
{
  "path": "doc://test.txt",
  "content": "..."
}

list_files:
{
  "path": "doc://"
}

run_shell:
{
  "command": "ls"
}

rag_search:
{
  "query": "..."
}

=========================
ФАЙЛОВАЯ СИСТЕМА
=========================

- doc:// → workspace/docs/
- file:// → workspace/
- если путь без префикса → считать doc://

ПРИМЕРЫ:

"прочитай test.txt"
→ doc://test.txt

"создай файл a.txt"
→ doc://a.txt

"покажи файлы"
→ list_files doc://

=========================
ПРАВИЛА
=========================

- НЕ повторяй TOOL_RESULT в final ответе.
- Используй TOOL_RESULT только как внутренние данные.
- Никогда не отвечай текстом вне JSON
- Никогда не объясняй действия
- Всегда сначала думай через tool при работе с файлами
"""


class Agent:

    def __init__(
        self,
        model_name=MODEL_NAME,
        embed_model=EMBED_MODEL,
        docs_path=DOCS_PATH,
        db_path=DB_PATH,
        workspace=WORKSPACE
    ):

        self.model_name = model_name

        self.embed_model = embed_model

        self.docs_path = docs_path

        self.db_path = db_path

        self.workspace = os.path.realpath(workspace)

        self.retriever = None

        self.ensure_workspace()

        self.init_rag()

        self.tools = {
            "write_file": self.tool_write_file,
            "read_file": self.tool_read_file,
            "list_files": self.tool_list_files,
            "run_shell": self.tool_run_shell,
            "rag_search": self.tool_rag_search
        }

    def resolve_path(self, path: str):

        path = path.strip()

        if path.startswith("doc://"):
            path = path[len("doc://"):]
            path = path.lstrip("/")
            path = os.path.join("docs", path)

        elif path.startswith("file://"):
            path = path[len("file://"):]
            path = path.lstrip("/")

        elif "/" not in path:
            path = os.path.join("docs", path)

        return self.safe_path(path)

    # =========================
    # WORKSPACE
    # =========================

    def ensure_workspace(self):

        os.makedirs(self.workspace, exist_ok=True)

    def safe_path(self, path: str):

        full_path = os.path.realpath(
            os.path.join(self.workspace, path)
        )

        if not full_path.startswith(self.workspace):
            raise Exception("access denied")

        return full_path

    # =========================
    # RAG
    # =========================

    def init_rag(self):

        print("🔧 Initializing RAG...")

        if not os.path.exists(self.docs_path):

            print("⚠ docs path not found")

            return

        all_docs = []

        for root, dirs, files in os.walk(self.docs_path):

            for file in files:

                path = os.path.join(root, file)

                docs = load_file(path)

                all_docs.extend(docs)

        if not all_docs:

            print("⚠ no documents found")

            return

        splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP
        )

        splits = splitter.split_documents(all_docs)

        print(f"📄 chunks: {len(splits)}")

        embeddings = OllamaEmbeddings(
            model=self.embed_model
        )

        if os.path.exists(self.db_path) and os.listdir(self.db_path):

            print("📦 loading existing db...")

            vectorstore = Chroma(
                persist_directory=self.db_path,
                embedding_function=embeddings
            )

        else:

            print("🧠 creating db...")

            vectorstore = Chroma.from_documents(
                documents=splits,
                embedding=embeddings,
                persist_directory=self.db_path
            )

            vectorstore.persist()

            print("✅ db saved")

        self.retriever = vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={
                "k": 4
            }
        )

        print("✅ RAG ready")

    # =========================
    # TOOLS
    # =========================

    def tool_read_file(self, path: str):
        real_path = self.resolve_path(path)
        return read_file(real_path)


    def tool_write_file(self, path: str, content: str):
        real_path = self.resolve_path(path)
        return write_file(real_path, content)

    def tool_list_files(self, path="."):

        safe = self.safe_path(path)

        return list_files(safe)

    def tool_run_shell(self, command: str):

        blocked = [
            "rm",
            "sudo",
            "reboot",
            "shutdown",
            "mkfs",
            "dd",
            ">",
            ">>",
            "|",
            "&"
        ]

        if any(b in command for b in blocked):

            return "blocked command"

        return run_shell(
            command=command,
            cwd=self.workspace
        )

    def tool_rag_search(self, query: str):

        if not self.retriever:

            return "RAG not initialized"

        docs = self.retriever.invoke(query)

        if not docs:

            return "nothing found"

        result = []

        for doc in docs:

            source = doc.metadata.get(
                "source",
                "unknown"
            )

            chunk = doc.page_content[:700]

            result.append(
                f"[source={source}]\n{chunk}"
            )

        return "\n\n---\n\n".join(result)

    # =========================
    # LLM
    # =========================

    def call_llm(self, messages):

        response = chat(
            model=self.model_name,
            messages=messages
        )

        return response["message"]["content"]

    # =========================
    # PARSER
    # =========================

    def parse_response(self, text: str) -> Dict[str, Any]:

        text = text.strip()

        try:

            data = json.loads(text)

            return data

        except Exception:

            return {
                "type": "error",
                "text": text
            }

    # =========================
    # EXECUTE TOOL
    # =========================

    def execute_tool(self, name: str, args: Dict):

        tool = self.tools.get(name)

        if not tool:

            return f"unknown tool: {name}"

        try:

            return tool(**args)

        except Exception as e:

            return f"tool error: {e}"

    # =========================
    # MAIN LOOP
    # =========================

    def clean_llm_output(text: str):

        # удаляем мусор до JSON
        start = text.find("{")
        end = text.rfind("}")

        if start == -1 or end == -1:
            return text

        return text[start:end+1]

    def run(self):

        print("🚀 Agent started")

        history: List[Dict] = []

        while True:

            user = input("\n>>> ")

            if user.lower() in ["exit", "quit"]:

                break

            messages = [
                {
                    "role": "system",
                    "content": SYSTEM_PROMPT
                },
                *history,
                {
                    "role": "user",
                    "content": user
                }
            ]

            step = 0
            print("Думаю...")
            while step < MAX_STEPS:

                response = self.call_llm(messages)

                parsed = self.parse_response(response)

                if parsed.get("type") == "final":

                    answer = parsed.get("text", "")

                    print(f"\n💬 {answer}")

                    history.append({
                        "role": "user",
                        "content": user
                    })

                    history.append({
                        "role": "assistant",
                        "content": answer
                    })

                    history = history[-MAX_HISTORY:]

                    break

                elif parsed.get("type") == "tool":

                    tool_name = parsed.get("name")

                    args = parsed.get("args", {})

                    result = self.execute_tool(
                        tool_name,
                        args
                    )

                    print("\nПочти готово...\n")

                    messages.append({
                        "role": "assistant",
                        "content": response
                    })

                    messages.append({
                        "role": "user",
                        "content": f"TOOL_RESULT:\n{result}"
                    })

                else:

                    print("\n⚠ invalid response")

                    print(parsed)

                    break

                step += 1

            if step >= MAX_STEPS:

                print("\n⚠ max steps reached")


if __name__ == "__main__":

    agent = Agent()

    agent.run()