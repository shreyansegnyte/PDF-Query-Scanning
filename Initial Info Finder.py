import openai, re
from PyPDF2 import PdfReader

openai.api_key = ""
pdfPath = "/Users/shreyansjain/Downloads/2022_ca_building_code_volumes_1_2_1st_ptg_rev.pdf"
# more pdfs: /Users/shreyansjain/Downloads/egnytepdfs
outputPath = "/Users/shreyansjain/Downloads/building_code_results.txt"
maxMatchesToSummarize = 20
maxSectionChars = 1000 # (per chunk)

# totalInputTokens = 0
# totalOutputTokens = 0

# def countTokensAndUpdate(usage):
    # global totalInputTokens, totalOutputTokens
    # totalInputTokens += usage['prompt_tokens']
    # totalOutputTokens += usage['completion_tokens']

def logGptCall(name, prompt, responseText):
    with open("gpt_log.txt", "a") as f: # /Users/shreyansjain/Downloads/gpt_log.txt
       # f.write(f"=== {name.upper()} ===\n") 
       # f.write("Prompt:\n" + prompt + "\n")
       # f.write("Response:\n" + responseText + "\n\n")
        return

def extractCoreQuery(userInput):
    # prompt = f'Here is the user's input: "{userInput}"\nOnly return a sentence or phrase in double quotes referring to the technical phrase or object that they are asking about.'
    prompt = f'The user said: "{userInput}"\nExtract the technical phrase or object they are asking about. Only return a phrase in double quotes.'
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        temperature=0 # between 0 and 0.1
       # temperature = 0.2 (roof -> ceiling)
    )
    # countTokensAndUpdate(result['usage'])
    print(result.choices[0].message.content.strip()) #ignore
    response = result.choices[0].message.content.strip()
    logGptCall("extractCoreQuery", prompt, response)
    return response.strip('"')

def expandQueryTerms(coreQuery):
    # prompt = f'The user is asking about: "{coreQuery}" - return a (important:)PYTHON LIST (nothing else) of related terms (maximum of 30). You must include the base word and not repeat terms'
    prompt = f'The user is asking about: "{coreQuery}".\nReturn a Python list of related terms (5–7 items). Include synonyms and variations. Make sure that the base word is included. Only output a valid Python list.'
    result = openai.ChatCompletion.create(
        model="gpt-3.5-turbo",
        messages=[{"role": "user", "content": prompt}],
        # keep temperature at 0.3 to avoid duplicate items in list
        # 0.25 < temp < 0.35
        temperature=0.3
    )
    # countTokensAndUpdate(result['usage'])
    response = result.choices[0].message.content.strip()
    logGptCall("expandQueryTerms", prompt, response)
    return eval(response)

def extractPdfSections(filepath):
    reader = PdfReader(filepath)
    sections = []
    for i, page in enumerate(reader.pages):
        text = page.extract_text()
        if text:
            paragraphs = text.split("\n\n")
            for para in text.split("\n\n"):
                if len(para) > 100: # !!! maxSectionChars = 1000
                    sections.append({
                        "sectionNum": len(sections) + 1,
                        "page": i + 1,
                        "text": para
                    })
    return sections

# tbd
# def searchSections(queryTerms, sections):
    # matches = []
    # for section in sections:
        # for term in queryTerms:
            # following part generated from chatgpt
            # if re.search(rf'\b{re.escape(term)}\b', section["text"], re.IGNORECASE):
                # matches.append(section)
                # break
            # return
    # return matches 
        # return

def summarizeSectionsWithQuotes(sections, coreQuery):
    for s in sections:
        text = s["text"]
        # length > max chars?
        # add prompt first
        prompt = {


            # tbd




        }

        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.2
        )
        # countTokensAndUpdate(response["usage"])
        print(response.choices[0].message.content.strip()) #ignore
        result = response.choices[0].message.content.strip()
        logGptCall("summarizeWithQuote", prompt, result)
        s["summaryWithQuote"] = result # FIXED
    return sections

# in progress:
def filterToBestSummaries(sections, coreQuery):
    joined = "\n\n".join([
        f"[Section {s['sectionNum']}] Page {s['page']}\n{s['summaryWithQuote']}"
    ])

    # logGptCall("filterFinalQuoted", prompt, responseText)
    
# in progress:
# goal is to basically sort through the summaries taken from the 20
# and write summaries
def writeSummariesToFile(filteredSections, filepath):
    with open(filepath, "w") as f:
        return
    print(f"Results saved to: {filepath}")

def main():

    userInput = input("prompt (full sentence): ").strip()
    coreQuery = extractCoreQuery(userInput)
    print("main poi:", coreQuery)
    queryTerms = expandQueryTerms(coreQuery)

    print("extended poi list:", queryTerms)
    print("finding matches in pdf")
    allSections = extractPdfSections(pdfPath)


    # selected top 20 matches so that takes less time
    # maxMatchesToSummarize = 20


   # no fallback
   # check chatgpt for fallback code
   # https://chatgpt.com/c/684749b6-3790-8002-853b-bc59d285dd3f
   # quotedSummaries = summarizeSectionsWithQuotes(topMatches, coreQuery)
   # bestSummaries = filterToBestSummaries(quotedSummaries, coreQuery)
   # writeSummariesToFile(bestSummaries, outputPath) 
    # printCostSummary()


main()