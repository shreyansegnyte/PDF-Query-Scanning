import tkinter as tk
from tkinter import ttk, scrolledtext
import time
import os
from PyPDF2 import PdfReader
from sentence_transformers import SentenceTransformer
import chromadb
from chromadb.config import Settings
import openai
import re
import tiktoken  # NEW

# --- Config ---
# had to generate a new api key because the original one from github got auto-deleted
openai.api_key = "" 
PDF_PATH = "/Users/shreyansjain/Documents/pdfscanning/118599_SPECS.pdf"
DB_DIR = "chromadb_store"
COLLECTION_NAME = "pdf_paragraphs"
BATCH_SIZE = 100

# --- Helper: Token Counter ---
def count_tokens(text, model="gpt-4"):
    enc = tiktoken.encoding_for_model(model)
    return len(enc.encode(text))

# --- GUI setup ---
class PDFRAGApp:
    def __init__(self, root):
        self.root = root
        root.title("PDF parser/searcher w/ RAG")

        self.query_label = tk.Label(root, text="Enter your query:")
        self.query_label.pack()

        self.query_entry = tk.Entry(root, width=50)
        self.query_entry.pack()

        self.output = scrolledtext.ScrolledText(root, width=100, height=25, wrap=tk.WORD)
        self.output.pack()

        self.progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=600)
        self.progress.pack(pady=5)

        self.timer_label = tk.Label(root, text="Time elapsed: 0 s")
        self.timer_label.pack()

        self.answer_button = tk.Button(root, text="Get Answer", command=self.get_answer)
        self.answer_button.pack(pady=5)

        self.start_time = None
        self.collection = None
        self.metadata = []

        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.chroma_client = chromadb.PersistentClient(path=DB_DIR)

        self.root.after(100, self.run_pipeline)

    def log(self, msg):
        self.output.insert(tk.END, msg + "\n")
        self.output.see(tk.END)
        self.root.update()

    def update_timer(self):
        if self.start_time:
            elapsed = int(time.time() - self.start_time)
            self.timer_label.config(text=f"Time elapsed: {elapsed} s")
            self.root.after(1000, self.update_timer)

    def extract_paragraphs(self):
        self.log("Extracting text from PDF...")
        reader = PdfReader(PDF_PATH)
        paragraphs = []
        metadata = []
        total_pages = len(reader.pages)

        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                for raw in text.split('\n'):
                    p = ' '.join(raw.strip().split())  # Collapse whitespace
                    if len(p) > 30:  # Ignore short fragments
                        paragraphs.append(p)
                        metadata.append({"page": i + 1})  # 1-based index
            self.progress["value"] = (i + 1) / total_pages * 100
            self.root.update()

        return paragraphs, metadata

    def run_pipeline(self):
        self.start_time = time.time()
        self.update_timer()

        self.log("Setting up vector database...")

        try:
            self.collection = self.chroma_client.get_or_create_collection(COLLECTION_NAME)
        except:
            self.log("Failed to connect to Chroma. Exiting.")
            return

        if self.collection.count() > 0:
            self.log("Database already loaded. ✅ Ready for query input.")
            return

        paragraphs, metadata = self.extract_paragraphs()
        total = len(paragraphs)

        for i in range(0, total, BATCH_SIZE):
            batch = paragraphs[i:i+BATCH_SIZE]
            meta_batch = metadata[i:i+BATCH_SIZE]
            ids = [f"p{i+j}" for j in range(len(batch))]
            self.log(f"Embedding batch {i // BATCH_SIZE + 1}...")
            embeddings = self.embed_model.encode(batch, show_progress_bar=False)
            self.collection.add(documents=batch, embeddings=embeddings, ids=ids, metadatas=meta_batch)
            self.progress["value"] = (i + len(batch)) / total * 100
            self.root.update()

        self.log("✅ Ready for query input.")

    def get_answer(self):
        query = self.query_entry.get().strip()
        if not query:
            self.log("Please enter a query.")
            return

        self.log(f"Processing query: '{query}' & searching database...")

        try:
            results = self.collection.query(
                query_texts=[query],
                n_results=5,
                include=["documents", "metadatas"]
            )
        except Exception as e:
            self.log(f"Error querying Chroma: {e}")
            return

        documents = results["documents"][0]
        metadatas = results["metadatas"][0]

        formatted_refs = []
        for doc, meta in zip(documents, metadatas):
            page = meta.get("page", "?")
            section = self.extract_section(doc)
            ref = f"Page {page}" + (f", Section {section}" if section else "")
            formatted_refs.append(ref)

        inline_citations = "; ".join(formatted_refs)

        self.log("Loading query into gpt-4.1-nano-2025-04-14...")

        prompt = f"""You are an expert on the topics in the intial PDF provided in this RAG pipeline.
Answer the following question clearly and concisely in a single paragraph.
Use your expert knowledge and integrate the relevant references directly into the explanation.
Do not include quotes. Cite no more than 5 references like (Page X, Section Y).

Question: {query}

Relevant citations: {inline_citations}
"""

        # Token tracking
        prompt_tokens = count_tokens(prompt)
        self.log(f"Input prompt: {prompt_tokens} tokens")

        try:
            response = openai.ChatCompletion.create(
                model="gpt-4.1-nano-2025-04-14",
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            answer = response.choices[0].message.content.strip()
            answer_tokens = count_tokens(answer)
            total_tokens = prompt_tokens + answer_tokens

            self.log(f"Output: {answer_tokens} tokens")
            self.log(f"Total: {total_tokens} tokens")

        except Exception as e:
            answer = f"Error from OpenAI: {e}"

        self.log("\nResponse:")
        self.log(answer)

    def extract_section(self, text):
        match = re.search(r'(Section|§)\s*([\dA-Za-z\.-]+)', text)
        if match:
            return match.group(2)
        return None

# --- Run the app ---
# dml
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFRAGApp(root)
    root.mainloop()
