import os
from PyPDF2 import PdfReader
from PyPDF2 import PdfWriter

# prgm will NOT store output folder here
# instead it will store at file path of execution env in vscode
inputPath = "/Users/shreyansjain/Downloads/2022_ca_building_code_volumes_1_2_1st_ptg_rev.pdf"
outputPath = "/Users/shreyansjain/Downloads"
pagesPerChunk = 30  # Number of pages per chunk

reader = PdfReader(inputPath)
totalPages = len(reader.pages)

baseName = os.path.splitext(os.path.basename(inputPath))[0]
outputDir = os.path.join(outputPath, f"Chunked PDFs for {baseName[:10]}... (.pdf, {pagesPerChunk}pgs each)")  # makes folder name
os.makedirs(outputDir, exist_ok=True)

writer = PdfWriter() # new pdf (blank)
chunkIndex = 1 #organize pdfs in order

for pageIndex in range(totalPages): 
    # total pages of ORIGINAL pdf
    writer.add_page(reader.pages[pageIndex]) 

    # Save the chunk if we reached pagesPerChunk or last page
    if len(writer.pages) >= pagesPerChunk or pageIndex == totalPages - 1:
        chunkName = f"chunk {chunkIndex}.pdf" 
        chunkPath = os.path.join(outputDir, chunkName)

        with open(chunkPath, "wb") as outputFile: #wb = write bytes
            writer.write(outputFile)

        print(f"saved {chunkName} in {outputPath}/{baseName[:10]}...")
        writer = PdfWriter() # blank slate
        chunkIndex += 1
