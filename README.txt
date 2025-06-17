This documentation is explaining the concepts in the file "Fixed PDF into finder.py".
Goal: to efficiently look/search/sort through a PDF based on a user's query and return a correct/specific answer to their
question without being redundant, including citations and sources for another model to read for RAG

Code explanation:
1. Firstly, the user's initial input is sorted for "core queries"; typos are removed, grammatical issues are fixed, and using gpt-3.5, a core query/set of core queries is generated. Here is an example:
-
input: "I am looking for information about roofing regulations and laws surrounding roofs from a context of fires/wildfires in the pdf."
generated "core queries": ['roofing regulations', 'fire-resistant roofing', 'roof fire standards', 'wildfire prevention measures', 'roofing materials codes', 'fire-safe roofs', 'building codes for roofs'] * temperature is a bit lower because we don't want it to "make things up" in this step

2. Then, another interation of gpt-3.5 uses these generated "sub-core-queries" to make a list of search terms related to each of the sub-core-queries to be found in the PDF using the PyPDF2 module. For example, picking one of the  items of the list above: 
-
input: fire-safe roofs
extended list generated: ['fire-resistant roofs', 'flame-retardant roofs', 'ignition-resistant roofs', 'fireproof roofs', 'non-combustible roofs'] * higher temperature: allows for more "creative" search terms that are more spread out than ones in step #1

3. After this, the PDF is chunked by characters into sections to then be processed by PyPDF2 with the terms above. When/if one matches, the area is 'marked' (stored) as a match. For example:
-
Core-sub-query "building codes for roofs"/core-query building codes: PDF is searched for the 7-20 words in the extended list as explained in step #2. The output is 55 matches throughout the PDF which are stored to be evaluated in the next step.

4. Once the sections/chunks are marked for review, another interation of gpt-3.5 goes through each of them, generating a summary of the items mentioned, focusing on quantitative data and specific details in its output. Through this step, on average, around 200-1500 summaries are generated based on the amount of matches which occured from step #3. 

5. If there are at least 20 summaries generated (most of the time) from step #4:
    a. gpt-3.5 goes through all of them, matching them with a "fuzzy idea": the intial core query(ies)
    b. based on the best ones it finds, it deletes the remaining ones until 20 are left
    c. the remaining summaries/quotations now only contain information from the context of the original query
    * it's temperature is relatively high so that it can be more "creative" than normal

6. Now, gpt-3.5 loops over these 20 summaries, finding the top 3-5 ones which are as specific as possible. Sometimes, if the initial core query is extremely specific, this step (and #5) are never reached. In general, however, this step then proceeds to  delete the remaining summaries/quotes and only keep 3-5. * has a low temperature because no creativity is required here

7. Finally, gpt-3.5 combines the summaries and quotes previously generated, making a full "argument" / "answer": to do this, it looks back in the PDF at the coressponding sections and pulls quotes/specific information to its answer to be as accurate as possible. It returns a long paragraph using a tkinter GUI messagebox.
-
For our case, here is the output: "In the context of fires and wildfires, the California Building Code mandates strict regulations regarding roofing materials to enhance fire resistance and reduce the risk of fire spreading. Section 1507.2, 1507.3, and 1507.4 emphasize that roof coverings, assemblies, and systems must be designed and installed in accordance with the code and manufacturer's instructions. The code classifies roofing materials as Class A, B, or C based on their fire resistance, as outlined in Section 1. In high fire hazard severity zones, as specified in Section 2, fire-resistant roofing materials are required to meet specific standards to mitigate fire risks. Proper installation of these materials, as addressed in Section 3, is crucial for their effectiveness in reducing fire damage. Additionally, Section 1381 outlines standards for roof fire safety, including requirements for exterior walls of buildings in various construction types. For new buildings in Fire Hazard Severity Zones or Wildland Interface Fire Areas, Section 354 mandates specific materials and construction methods to prevent wildfires. Sections 854, 855, and 856 provide detailed requirements for roofing materials, including testing standards, classification, and fire-retardant properties. The California Building Code has been updated to enforce fire-safe roofs in designated areas prone to wildfires, aiming to enhance building safety and resilience against fire hazards. These regulations are crucial for ensuring the protection of structures and occupants in high-risk fire zones, aligning with the state's commitment to fire prevention and safety measures." * highest temperature to allow for a unique and creative output

8. Then, this large paragraph is condensed down by a final gpt-3.5 instance prompted to stay specific but still also remain accurate; this simulates an actual/real user output.

Other comments: in the previous version of this file (6/10), there used to be a logging feature where gpt-3.5 would paste all relevant parts of the PDF that it analyzed into a text file. However, it would get so big (500,000+ lines) that it slowed the program down substantially so I decided to remove it. Now, if you would like to view what's actually being processed, feel free to add a simple "print()" block in the various gpt-centered functions. If you would like to test the code, I can you send you the API key.
* quick detail: when running, if there's an error on lines 32/45, just re-run the code because sometimes, gpt-3.5 returns an incorrectly structured python list which can cause errors in the following functions

Update; 6/12: changing models from gpt-3.5-turbo did not affect the API costs much. However, after evaluating 3.5-turbo and 4.1-nano (with 4.1), I decided to change all of them to 4.1-nano because the evaluation pass rate changes from 59% to 92% when moving from 3.5 to 4.1.