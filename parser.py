import re
from docx import Document
DATA_SOURCE_MASTER = {
    # PREMIER
    "premier healthcare database": "Premier Healthcare Database",
    "pinc ai": "Premier Healthcare Database",

    # OPTUM
    "optum clinformatics date of death": "Optum DOD/SES",
    "optum clinformatics": "Optum",
    "optum dod": "Optum DOD/SES",
    "optum ses": "Optum DOD/SES",

    # MARKETSCAN
    "ibm marketscan": "IBM Marketscan",
    "ccae": "IBM Marketscan",
    "mdcr": "IBM Marketscan",
    "mdcd": "IBM Marketscan",

    # OTHERS
    "mercy": "Mercy",
    "truveta": "Truveta",
    "flatiron": "Flatiron",
    "concert ai": "Concert AI",
    "komodo": "Komodo",
    "cprd": "CPRD",
    "hes": "HES",
    "salford": "Salford Royal",
    "jmdc": "JMDC",
    "loopback": "Loopback",
    "integra": "Integra",
    "healthverity": "HealthVerity",
    "connect": "Connect"
}

def read_docx(file):
    doc = Document(file)
    text = []

    for para in doc.paragraphs:
        if para.text.strip():
            text.append(para.text.strip())

    return "\n".join(text)


def extract_study_selection(text):

    text_lower = text.lower()

    start_keywords = ["study design", "study population", "inclusion criteria"]
    end_keywords = ["exposure variable","primary independent variable", "covariates", "study outcomes","exposure variable","product codes"]

    start_idx = None
    end_idx = None

    for kw in start_keywords:
        match = re.search(kw, text_lower)
        if match:
            start_idx = match.start()
            break

    if start_idx is None:
        return text

    for kw in end_keywords:
        match = re.search(kw, text_lower[start_idx:])
        if match:
            end_idx = start_idx + match.start()
            break

    if end_idx is None:
        end_idx = len(text)

    return text[start_idx:end_idx]


def split_criteria_sections(text):

    text_lower = text.lower()
    if "table of contents" in text_lower:
        text = text.split("table of contents")[-1]

    #finding matches for both inclusion and exclusion criteria
    inc_matches = list(re.finditer(r"inclusion criteria", text_lower))
    exc_matches = list(re.finditer(r"exclusion criteria", text_lower))

    inc_start = inc_matches[-1].start() if inc_matches else -1
    exc_start = exc_matches[-1].start() if exc_matches else -1

    if inc_start == -1:
        inclusion_text = ""
    else:
        inclusion_text = text[
            inc_start : exc_start if exc_start != -1 else len(text)
        ]

    if exc_start == -1:
        exclusion_text = ""
    else:
        exclusion_text = text[exc_start:]

    return inclusion_text, exclusion_text


def extract_steps(section_text):

    raw_steps = section_text.split("\n")

    steps = []

    for step in raw_steps:

        step = step.strip()
        step_lower = step.lower()

        if len(step) < 15:
            continue

        # remove headings only
        if "inclusion criteria" in step_lower:
            continue
        if "exclusion criteria" in step_lower:
            continue
        if "patients will be included" in step_lower:
            continue    
        if "patients will be excluded" in step_lower:
            continue    
        if "table of contents" in step_lower:
            continue    

        # remove unwanted line
        if step_lower.startswith("individuals") or step_lower.startswith("see")or step_lower.startswith("product codes") :
            continue
        
        #specific lines
        if  " must meet all the following" in step_lower:
            continue
        if " meeting any of the following" in step_lower: 
            continue
        # remove numbering
        step = re.sub(r'^\d+\.\s*', '', step)

        steps.append(step)

    return steps


def parse_protocol(file):

    text = read_docx(file)
    data_sources = detect_data_source(text)
    study_section = extract_study_selection(text)

    inc_text, exc_text = split_criteria_sections(study_section)

    inc_steps = extract_steps(inc_text)
    exc_steps = extract_steps(exc_text)

    # build attrition
    attrition = []
    step_no = 1

    for step in inc_steps:
        attrition.append((step_no, "inclusion", step))
        step_no += 1

    for step in exc_steps:
        attrition.append((step_no, "exclusion", step))
        step_no += 1

    return inc_steps, exc_steps, attrition, data_sources

def extract_data_source_section(text):
    import re

    text_lower = text.lower()

    start = re.search(r"data sources?", text_lower)
    if not start:
        return ""

    start_idx = start.start()

    end_patterns = [
        "study design",
        "study population",
        "endpoints",
        "data analyses"
    ]

    end_idx = len(text)

    for pattern in end_patterns:
        match = re.search(pattern, text_lower[start_idx:])
        if match:
            end_idx = start_idx + match.start()
            break

    return text[start_idx:end_idx]


def detect_data_source(text):

    section = extract_data_source_section(text)
    section_lower = section.lower()

    detected = []

    sorted_keys = sorted(DATA_SOURCE_MASTER.keys(), key=len, reverse=True)

    for key in sorted_keys:
        pattern = r"\b" + re.escape(key) + r"\b"

        if re.search(pattern, section_lower):
            detected.append(DATA_SOURCE_MASTER[key])

            section_lower = re.sub(pattern, "", section_lower)

    return list(set(detected))
