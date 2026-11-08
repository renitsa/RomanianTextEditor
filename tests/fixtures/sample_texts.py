"""
Reusable sample texts for testing.
Organized by language and use case.
"""

# Romanian samples
ROMANIAN_SIMPLE = "Acesta este un text simplu în română."

ROMANIAN_WITH_ABBREVIATIONS = """
Dr. Popescu a venit azi. Dna. Maria a plecat devreme.
Dl. Ion lucrează pe str. Victoriei nr. 10.
Prof. Ionescu predă la univ. din București.
"""

ROMANIAN_MULTI_PARAGRAPH = """
Primul paragraf conține mai multe propoziții. 
Aceasta este a doua propoziție din primul paragraf.

Al doilea paragraf este separat prin linie goală.
Și el are mai multe propoziții.

Al treilea paragraf este scurt.
"""

ROMANIAN_COMPLEX = """
Text complex pentru testare. Conține diverse elemente!
Are întrebări? Desigur! Are și exclamații!

Include și abrevieri: Dr. Popescu, str. Victoriei, etc.
Numerele apar: 123, 45.67, 89%.

Caractere speciale: @#$%^&*()
Unicode: café, naïve, résumé.
"""

# English samples
ENGLISH_SIMPLE = "This is a simple text in English."

ENGLISH_WITH_ABBREVIATIONS = """
Dr. Smith came today. Mrs. Johnson left early.
Mr. Brown works on St. Mary's Street No. 10.
Prof. Davis teaches at the Univ. of London.
"""

ENGLISH_MULTI_PARAGRAPH = """
First paragraph contains several sentences.
This is the second sentence of the first paragraph.

The second paragraph is separated by an empty line.
It also has multiple sentences.

The third paragraph is short.
"""

# Edge cases
EMPTY_TEXT = ""

SINGLE_SENTENCE = "Just one sentence."

VERY_LONG_TEXT = "Lorem ipsum dolor sit amet. " * 200  # ~5000 chars

TEXT_WITH_NO_PUNCTUATION = "this text has no punctuation marks at all just words"

TEXT_ONLY_PUNCTUATION = "...!!!???...!!!"

# Special characters
TEXT_WITH_NEWLINES = "Line 1\nLine 2\n\nLine 3\n\n\nLine 4"

TEXT_WITH_TABS = "Column1\tColumn2\tColumn3"

TEXT_MIXED_ENCODINGS = "Café, naïve, résumé, Москва, 北京, العربية"

# Error cases
NONE_TEXT = None

# Chunking test cases
CHUNKING_TEST_CASES = {
    "small_chunks": ["Chunk 1", "Chunk 2", "Chunk 3"],
    "varied_sizes": ["Small", "Medium sized chunk here", "A very long chunk that exceeds normal size limits and should be handled appropriately by the chunking strategies"],
    "empty_chunks": ["", "Not empty", "", "", "Also not empty", ""],
    "single_chunk": ["Only one chunk"],
    "many_small": [f"Chunk {i}" for i in range(1, 51)],  # 50 small chunks
}
