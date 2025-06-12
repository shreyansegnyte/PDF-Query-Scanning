import openai, re
from PyPDF2 import PdfReader
import tkinter as tk
from tkinter import messagebox

openai.api_key = "" # github will not allow me to keep the api key in my code
pdfPath = "" # please change the PDF path from wherever it is on your computer
# here is a link to the PDF I have been using to test this (also in github repo):
# https://egnyte.egnyte.com/dl/jWFdFRBrwT7t/2022_ca_building_code_volumes_1_2_1st_ptg_rev.pdf_
maxMatchesToSummarize = 20
maxSectionChars = 1000

# def logGptCall(name, prompt, responseText):
    # return 

def extractCoreSubQueries(userInput):
    prompt = f'''
The user input is: "{userInput}"
Break this into multiple focused technical sub-queries, especially if multiple concepts are present.
Include base words or initial main core concepts: an input of "roofing regulations" means that you have to include "roof" in your output!
Return only a valid Python list of quoted strings, like:
["roofing regulations", "fire-resistant roofing", "roof fire standards"]
Do NOT copy the list above. Please generate your own.
DO NOT number them. DO NOT add any explanations. Python list only.
You MUST include the base word / words in your output. For example, "roofing regulations" -> "roof" must be included.
One more time: it MUST be a python list and MUST have at least 5 elements.
'''
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=1
    )
    response = result.choices[0].message.content.strip()
    # logGptCall("extractCoreSubQueries", prompt, response)
    return eval(response)


def extractCoreQuery(subQuery):
    prompt = f'The sub-query is: "{subQuery}".\nExtract the technical engineering phrase or object being asked about. Only return a phrase in double quotes. It must not have any numbers attached to it. Just the phrase.'
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.1 # want it to be highly accurate but ready for typos
    )
    return result.choices[0].message.content.strip().strip('"')

def expandQueryTerms(coreQuery):
    prompt = f'The user is asking about: "{coreQuery}".\nReturn a Python list (PYTHON LIST ONLY) of related terms (5–7 items). It MUST be a python list (for example: [term1, term2, term3]). Nothing else. Include synonyms and variations. Make sure the base word is included.'
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.35  # want it to get creative but not too much
    )
    return eval(result.choices[0].message.content.strip())

def extractPdfSections(filepath):
    reader = PdfReader(filepath)
    sections = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            paragraphs = text.split("\n\n")
            for para in paragraphs:
                para = para.strip()
                if len(para) > 100:
                    sections.append({
                        "sectionNum": len(sections) + 1,
                        "page": i + 1,
                        "text": para
                    })
    return sections

def searchSections(queryTerms, sections):
    matches = []
    for section in sections:
        for term in queryTerms:
            if re.search(rf'\b{re.escape(term)}\b', section["text"], re.IGNORECASE):
                matches.append(section)
                break
    return matches

def summarizeSectionsWithQuotes(sections, coreQuery):
    for s in sections:
        text = s["text"]
        if len(text) > maxSectionChars:
            text = text[:maxSectionChars] + " [...]"
        prompt = f'The following is a paragraph from a PDF (starts on page {s["page"]}).\n\nPlease:\n1. Write a clear, focused summary about "{coreQuery}" only, based on the information in this summary\n2. Then quote 2–3 sentences directly from the paragraph that best illustrate the topic\n3. Don\'t quote summary-style statements. Keep it direct from the PDF. Do not include external information. If none is found in the PDF, explain that nothing was found in the PDF.\n\nText:\n{text}'
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2 # don't want it to make things up
        )
        s["summaryWithQuote"] = response.choices[0].message.content.strip()
    return sections

def filterToBestSummaries(sections, coreQuery):
    joined = "\n\n".join([
        f"[Section {s['sectionNum']}] Page {s['page']}\n{s['summaryWithQuote']}"
        for s in sections
    ])
    prompt = f'The user is asking specifically about: "{coreQuery}" from a PDF.\n\nFrom these summaries and quotes, pick only the 3–4 sections that are:\n- Highly relevant to the query\n- Not general background\n- Contain directly useful information with quotes\n\nOnly return: [{{"section": int, "page": int, "summaryWithQuote": str}}]\n\nSummaries and quotes:\n{joined}'
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    try:
        return eval(response.choices[0].message.content.strip())
    except Exception:
        return []

def generateFinalAnswer(coreQuery, filteredSections):
    content = "\n\n".join([
        f"Section {s['section']} (Page {s['page']}):\n{s['summaryWithQuote']}"
        for s in filteredSections
    ])
    prompt = f'You are an expert in engineering.\nThe user asked about: "{coreQuery}"\n\nBased on the following summaries and quotes from the PDF, write a clear, accurate, long, one-paragraph answer for the user. It must include a lot of detailed quantitative information from the original PDF including numbers (if applicable). Make sure that it is not a diversion from the original core query: {coreQuery}. It should also include page numbers and chapters of findings, if applicable. It should only include information from the PDF and summaries itself, not any external info.\n\nSummaries and Quotes:\n{content}'
    response = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.2
    )
    return response.choices[0].message.content.strip()


#def finalAnswer(txt, userInput):
    #prompt = f'Generate a short one-to-two-sentence long report based on this summary: {txt}. Only keep quantitative data/numbers when needed for clarity and combine repeated sections. Make sure that this report is solely based off of the inputted text and not any external or general information. It should also directly corelate to the original queries of the user: "{userInput}"'
    #response = openai.ChatCompletion.create(
        #model="gpt-3.5-turbo",
        #messages=[{"role": "user", "content": prompt}],
        #temperature=0.2)
    #return response.choices[0].message.content.strip()

def showAnswerPopup(answerText):
    root = tk.Tk()
    root.withdraw()  
    messagebox.showinfo("Response Answer", answerText)
    root.destroy()
    # above code generates response as a text box rather than in terminal
    # may look different than on my end if done on windows
def main():
    userInput = input("Prompt (full sentence): ").strip()
    print("Breaking input into focused sub-queries...")
    subQueries = extractCoreSubQueries(userInput)
    print("Sub-queries:", subQueries)
    print("Please wait 5-15 seconds...")

    allSections = extractPdfSections(pdfPath)

    allFilteredResults = []

    for sub in subQueries:
        print("\nProcessing sub-query:", sub)
        coreQuery = extractCoreQuery(sub)
        print("Core query term:", coreQuery)

        queryTerms = expandQueryTerms(coreQuery)
        print("Extended POI list:", queryTerms)

        matchingSections = searchSections(queryTerms, allSections)
        if len(matchingSections) > 0:
            print(f"{len(matchingSections)} matches for '{sub}'")
            print("Please wait a few seconds...")
        else:
            print("Please wait a few seconds...")
        topMatches = matchingSections[:maxMatchesToSummarize]
        quotedSummaries = summarizeSectionsWithQuotes(topMatches, coreQuery)
        bestSummaries = filterToBestSummaries(quotedSummaries, coreQuery)

        for bs in bestSummaries:
            allFilteredResults.append(bs)
        
        # bs :)


    # logging disabled

    if allFilteredResults:
        print("\nGenerating final combined answer...")
        combinedAnswer = generateFinalAnswer(userInput, allFilteredResults)
        #finalAnswerLast = finalAnswer(combinedAnswer, subQueries)
        print("\nFinal Answer:\n")
        #print(finalAnswerLast)
        print(combinedAnswer)
        #showAnswerPopup(finalAnswerLast)
        showAnswerPopup(combinedAnswer)
    else:
        print("\nNo relevant content found in the PDF. Generating a standard/background information-based answer instead...")



main()

# goal for next time is to make this program work well for ANY pdf
# for example, right now, the instructions are tuned very well for this
# california building code PDF. it does not work well for a PDF about
# something completely different yet engineering related