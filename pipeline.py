import tkinter as tk
from tkinter import ttk, scrolledtext
import time
import os
from sentence_transformers import SentenceTransformer
from PyPDF2 import PdfReader
import chromadb
import openai

# --- Config ---
PDF_PATH = "/Users/shreyansjain/Documents/pdfscanning/2022_ca_building_code_volumes_1_2_1st_ptg_rev.pdf"
DB_DIR = "/Users/shreyansjain/Documents/pdfscanning/chromadb_store"
OPENAI_KEY = ""
BATCH_SIZE = 100

# --- GUI App ---
class PDFRAGApp:
    def __init__(self, root):
        self.root = root
        root.title("PDF RAG Assistant with Progress Bar")

        self.query_label = tk.Label(root, text="Enter your query:")
        self.query_label.pack()

        self.query_entry = tk.Entry(root, width=100)
        self.query_entry.pack()

        self.output = scrolledtext.ScrolledText(root, width=100, height=20)
        self.output.pack()

        self.progress = ttk.Progressbar(root, orient="horizontal", mode="determinate", length=600)
        self.progress.pack(pady=5)

        self.timer_label = tk.Label(root, text="Time elapsed: 0 s")
        self.timer_label.pack()

        self.answer_button = tk.Button(root, text="Get Answer", command=self.get_answer)
        self.answer_button.pack(pady=5)

        self.start_time = None
        self.embed_model = SentenceTransformer("all-MiniLM-L6-v2")
        self.chroma_client = chromadb.PersistentClient(path=DB_DIR)
        self.collection = self.chroma_client.get_or_create_collection(name="pdf_paragraphs")

        self.root.after(100, self.run_pipeline)

    # def log(self, msg):
        # self.output.insert(tk.END, msg + "\n")
        # self.output.see(tk.END)
        # self.root.update()

    def log(self, msg):
        self.output.insert(tk.END, msg + "\n")
        self.output.see(tk.END)
        self.root.update()

    def update_timer(self):
        if self.start_time:
            elapsed = round(time.time() - self.start_time, 2)
            self.timer_label.config(text=f"Time elapsed: {elapsed} s")
            self.root.after(500, self.update_timer)

    def run_pipeline(self):

        self.start_time = time.time()
        self.update_timer()

        self.log("Extracting text from PDF...")
        paragraphs = self.extract_paragraphs(PDF_PATH)
        total = len(paragraphs)

        existing_count = self.collection.count()
        self.log(f"Existing items in DB: {existing_count}/{total}")

        for i in range(existing_count, total, BATCH_SIZE):
            batch = paragraphs[i:i+BATCH_SIZE]
            self.log(f"Embedding batch {i//BATCH_SIZE + 1}")
            embeddings = self.embed_model.encode(batch, show_progress_bar=False)
            ids = [f"p{i+j}" for j in range(len(batch))]
            self.collection.add(ids=ids, documents=batch, embeddings=embeddings)
            self.collection.persist()
            self.progress["value"] = (i + len(batch)) / total * 100
            self.root.update()

        self.progress["value"] = 100
        self.log("Pipeline ready. You can enter queries now.")

    def extract_paragraphs(self, path):
        reader = PdfReader(path)
        paragraphs = []
        total_pages = len(reader.pages)
        for i, page in enumerate(reader.pages):
            text = page.extract_text()
            if text:
                paras = [p.strip() for p in text.split('\n') if p.strip()]
                paragraphs.extend(paras)
            self.progress["value"] = (i + 1) / total_pages * 100
            self.log(f"Processed page {i + 1}/{total_pages}")
            self.root.update()
        return paragraphs

    def get_answer(self):
        query = self.query_entry.get().strip()
        if not query:
            self.log("Please enter a query.")
            return

        self.log(f"Processing query: {query}")

        results = self.collection.query(query_texts=[query], n_results=3)
        docs = results['documents'][0]
        context = "\n".join(docs)

        self.log("Sending query to OpenAI...")
        openai.api_key = OPENAI_KEY
        response = openai.ChatCompletion.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are an expert assistant that answers questions based on provided text."},
                {"role": "user", "content": f"Context:\n{context}\n\nQuestion: {query}"}
            ]
        )

        answer = response['choices'][0]['message']['content']
        self.log("Answer:\n" + answer)

# --- Run the app ---
if __name__ == "__main__":
    root = tk.Tk()
    app = PDFRAGApp(root)
    root.mainloop()
