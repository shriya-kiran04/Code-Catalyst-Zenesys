import io
import re
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from pypdf import PdfReader
import fitz
import pytesseract
from PIL import Image


# ============================================================
# APPLICATION
# ============================================================

app = FastAPI(
    title="DocuSheild AI",
    description=(
        "AI-powered document intelligence API for "
        "document extraction, verification, evidence "
        "and document-grounded interaction."
    ),
    version="1.0.0"
)


# ============================================================
# CORS
# Allows your teammate's frontend to communicate with backend
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# TESSERACT
# ============================================================

pytesseract.pytesseract.tesseract_cmd = (
    r"C:\Program Files\Tesseract-OCR\tesseract.exe"
)


# ============================================================
# CURRENT DEMO DOCUMENT
#
# For P1 we only need ONE document.
# Later this can be replaced by database/S3/object storage.
# ============================================================

current_document = {
    "filename": None,
    "text": None,
    "pages": 0,
    "extraction_method": None,
    "analysis": None,
}


# ============================================================
# REQUEST MODELS
# ============================================================

class DocumentQuestion(BaseModel):
    question: str


# ============================================================
# ROOT
# ============================================================

@app.get("/")
def root():
    return {
        "message": "DocuSheild AI API is running",
        "status": "success",
        "version": "1.0.0"
    }


# ============================================================
# HEALTH CHECK
# ============================================================

@app.get("/health")
def health_check():
    return {
        "status": "healthy",
        "service": "DocuSheild AI backend"
    }


# ============================================================
# PDF TEXT + OCR EXTRACTION
# ============================================================

def extract_text_from_pdf(contents: bytes):
    """
    Extract text from a PDF.

    First:
        Try normal selectable PDF text.

    If no selectable text exists:
        Render each page as an image and run OCR.
    """

    # --------------------------------------------------------
    # 1. NORMAL PDF TEXT EXTRACTION
    # --------------------------------------------------------

    reader = PdfReader(
        io.BytesIO(contents)
    )

    text_parts = []

    for page in reader.pages:

        page_text = page.extract_text()

        if page_text:
            text_parts.append(
                page_text
            )

    text = "\n".join(text_parts).strip()

    if text:

        return {
            "text": text,
            "pages": len(reader.pages),
            "extraction_method": "pdf_text"
        }

    # --------------------------------------------------------
    # 2. OCR FOR SCANNED PDF
    # --------------------------------------------------------

    document = fitz.open(
        stream=contents,
        filetype="pdf"
    )

    ocr_parts = []

    for page_number, page in enumerate(document):

        # Render PDF page as high-resolution image
        pix = page.get_pixmap(
            matrix=fitz.Matrix(2, 2)
        )

        image = Image.frombytes(
            "RGB",
            [pix.width, pix.height],
            pix.samples
        )

        page_text = pytesseract.image_to_string(
            image
        )

        if page_text.strip():

            ocr_parts.append(
                f"--- Page {page_number + 1} ---\n"
                f"{page_text.strip()}"
            )

    document.close()

    ocr_text = "\n\n".join(
        ocr_parts
    ).strip()

    return {
        "text": ocr_text,
        "pages": len(reader.pages),
        "extraction_method": "ocr"
    }


# ============================================================
# DOCUMENT TYPE IDENTIFICATION
# ============================================================

def identify_document_type(text: str):

    text_lower = text.lower()

    if any(word in text_lower for word in [
        "tax invoice",
        "invoice no",
        "invoice number",
        "subtotal",
        "gst",
    ]):
        return "Invoice"

    if any(word in text_lower for word in [
        "certificate",
        "certifies that",
        "has successfully completed",
        "certificate no",
        "certificate number",
    ]):
        return "Certificate"

    if any(word in text_lower for word in [
        "receipt",
        "amount paid",
        "payment received",
        "cash receipt",
    ]):
        return "Receipt"

    if any(word in text_lower for word in [
        "purchase order",
        "purchase order no",
        "purchase order number",
        "po number",
        "po no",
    ]):
        return "Purchase Order"

    if any(word in text_lower for word in [
        "agreement",
        "contract",
        "terms and conditions",
    ]):
        return "Agreement / Contract"

    return "General Document"


# ============================================================
# FIELD EXTRACTION
# ============================================================

def extract_fields(text: str):

    fields = {}

    patterns = {

        "date": (
            r"(?:date|issued\s*on|issue\s*date)"
            r"[:\s-]*"
            r"([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})"
        ),

        "document_number": (
            r"(?:certificate\s*(?:no|number)"
            r"|invoice\s*(?:no|number)"
            r"|receipt\s*(?:no|number)"
            r"|purchase\s*order\s*(?:no|number)"
            r"|po\s*(?:no|number))"
            r"[:\s#-]*"
            r"([A-Z0-9/-]+)"
        ),

        "name": (
            r"(?:name|student\s*name|candidate)"
            r"[:\s-]*"
            r"([^\n]+)"
        ),

        "organization": (
            r"(?:organization|organisation|company|institution)"
            r"[:\s-]*"
            r"([^\n]+)"
        ),

        "vendor": (
            r"(?:vendor|supplier|seller)"
            r"[:\s-]*"
            r"([^\n]+)"
        ),

        "total": (
            r"(?:grand\s*total"
            r"|total\s*amount"
            r"|amount\s*payable"
            r"|total)"
            r"[:\s₹$-]*"
            r"([0-9,]+(?:\.[0-9]+)?)"
        ),
    }

    for field, pattern in patterns.items():

        match = re.search(
            pattern,
            text,
            re.IGNORECASE
        )

        if match:

            value = match.group(1).strip()

            # Prevent accidental huge matches
            if len(value) <= 150:

                fields[field] = value

    return fields


# ============================================================
# EXPECTED FIELDS
# ============================================================

def get_expected_fields(document_type: str):

    if document_type == "Invoice":

        return [
            "date",
            "document_number",
            "total"
        ]

    if document_type == "Certificate":

        return [
            "date",
            "name",
            "organization"
        ]

    if document_type == "Receipt":

        return [
            "date",
            "total"
        ]

    if document_type == "Purchase Order":

        return [
            "date",
            "document_number"
        ]

    if document_type == "Agreement / Contract":

        return [
            "date"
        ]

    return [
        "date"
    ]


# ============================================================
# EVIDENCE EXTRACTION
# ============================================================

def create_evidence(
    text: str,
    fields: dict
):

    evidence = []

    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for field, value in fields.items():

        supporting_line = None

        for line in lines:

            if value.lower() in line.lower():

                supporting_line = line
                break

        evidence.append({

            "field": field,

            "value": value,

            "evidence_text": (
                supporting_line
                if supporting_line
                else value
            ),

            "source": "Uploaded document",

            "confidence": "high"
        })

    return evidence


# ============================================================
# CONSISTENCY / ANOMALY ANALYSIS
# ============================================================

def check_consistency(text: str):

    issues = []

    # --------------------------------------------------------
    # DATE CHECK
    # --------------------------------------------------------

    date_matches = re.findall(
        r"(?:date|issued\s*on|issue\s*date)"
        r"[:\s-]*"
        r"([0-9]{1,2}[/-][0-9]{1,2}[/-][0-9]{2,4})",
        text,
        re.IGNORECASE
    )

    unique_dates = list(
        dict.fromkeys(date_matches)
    )

    if len(unique_dates) > 1:

        issues.append({

            "type": "date_inconsistency",

            "description": (
                "Multiple different dates "
                "were detected."
            ),

            "values": unique_dates
        })

    # --------------------------------------------------------
    # TOTAL CHECK
    # --------------------------------------------------------

    total_matches = re.findall(
        r"(?:grand\s*total"
        r"|total\s*amount"
        r"|amount\s*payable"
        r"|total)"
        r"[:\s₹$-]*"
        r"([0-9,]+(?:\.[0-9]+)?)",
        text,
        re.IGNORECASE
    )

    unique_totals = list(
        dict.fromkeys(total_matches)
    )

    if len(unique_totals) > 1:

        issues.append({

            "type": "total_inconsistency",

            "description": (
                "Multiple different total "
                "amounts were detected."
            ),

            "values": unique_totals
        })

    return issues


# ============================================================
# COMPLETE DOCUMENT ANALYSIS
# ============================================================

def analyze_document(text: str):

    document_type = identify_document_type(
        text
    )

    fields = extract_fields(
        text
    )

    expected_fields = get_expected_fields(
        document_type
    )

    missing_fields = [
        field
        for field in expected_fields
        if field not in fields
    ]

    consistency_issues = check_consistency(
        text
    )

    evidence = create_evidence(
        text,
        fields
    )

    checks = []

    # --------------------------------------------------------
    # INFORMATION CHECK
    # --------------------------------------------------------

    if fields:

        checks.append({

            "check": "Important information detected",

            "result": "PASS",

            "details": (
                f"{len(fields)} important "
                "field(s) identified."
            )
        })

    else:

        checks.append({

            "check": "Important information detected",

            "result": "REVIEW",

            "details": (
                "No recognized structured "
                "fields were detected."
            )
        })

    # --------------------------------------------------------
    # REQUIRED FIELD CHECK
    # --------------------------------------------------------

    if missing_fields:

        checks.append({

            "check": "Required information",

            "result": "REVIEW",

            "details": (
                "Potentially missing: "
                + ", ".join(missing_fields)
            )
        })

    else:

        checks.append({

            "check": "Required information",

            "result": "PASS",

            "details": (
                "Expected fields were detected."
            )
        })

    # --------------------------------------------------------
    # CONSISTENCY CHECK
    # --------------------------------------------------------

    if consistency_issues:

        checks.append({

            "check": "Consistency analysis",

            "result": "REVIEW",

            "details": (
                "Potential conflicting "
                "values were detected."
            ),

            "issues": consistency_issues
        })

    else:

        checks.append({

            "check": "Consistency analysis",

            "result": "PASS",

            "details": (
                "No obvious conflicting "
                "values were detected."
            )
        })

    # --------------------------------------------------------
    # OVERALL STATUS
    # --------------------------------------------------------

    if not fields:

        overall_status = "REVIEW"

    elif missing_fields:

        overall_status = "REVIEW"

    elif consistency_issues:

        overall_status = "REVIEW"

    else:

        overall_status = "PASS"

    # --------------------------------------------------------
    # HUMAN-READABLE SUMMARY
    # --------------------------------------------------------

    if overall_status == "PASS":

        summary = (
            f"The {document_type.lower()} passed "
            "the available document checks."
        )

    else:

        summary = (
            f"The {document_type.lower()} requires "
            "review based on the available checks."
        )

    return {

        "document_type": document_type,

        "important_fields": fields,

        "verification": {

            "status": overall_status,

            "checks": checks
        },

        "missing_information": missing_fields,

        "consistency_issues": consistency_issues,

        "evidence": evidence,

        "summary": summary
    }


# ============================================================
# UPLOAD DOCUMENT
# ============================================================

@app.post("/documents/upload")
async def upload_document(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename provided."
        )

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    contents = await file.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    try:

        extraction = extract_text_from_pdf(
            contents
        )

        text = extraction["text"]

        if not text:

            return {

                "filename": file.filename,

                "pages": extraction["pages"],

                "extraction_method":
                    extraction["extraction_method"],

                "text": "",

                "status": "warning",

                "message": (
                    "Could not extract readable "
                    "text from this document."
                )
            }

        return {

            "filename": file.filename,

            "pages": extraction["pages"],

            "extraction_method":
                extraction["extraction_method"],

            "text": text,

            "status": "success",

            "message": (
                "Document uploaded and text "
                "extracted successfully."
            )
        }

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Could not process document: {str(e)}"
            )
        )


# ============================================================
# ANALYZE DOCUMENT
#
# This is the MAIN P1 endpoint.
#
# It:
# Uploads
# Extracts
# Understands
# Validates
# Generates evidence
# Stores document for Q&A
# ============================================================

@app.post("/documents/analyze")
async def analyze_uploaded_document(
    file: UploadFile = File(...)
):

    if not file.filename:

        raise HTTPException(
            status_code=400,
            detail="No filename provided."
        )

    if not file.filename.lower().endswith(".pdf"):

        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported."
        )

    contents = await file.read()

    if not contents:

        raise HTTPException(
            status_code=400,
            detail="Uploaded file is empty."
        )

    try:

        # ----------------------------------------------------
        # EXTRACT
        # ----------------------------------------------------

        extraction = extract_text_from_pdf(
            contents
        )

        text = extraction["text"]

        if not text:

            raise HTTPException(
                status_code=400,
                detail=(
                    "Could not extract readable "
                    "text from document."
                )
            )

        # ----------------------------------------------------
        # ANALYZE
        # ----------------------------------------------------

        analysis = analyze_document(
            text
        )

        # ----------------------------------------------------
        # STORE CURRENT DOCUMENT
        #
        # Used by /documents/ask
        # ----------------------------------------------------

        current_document["filename"] = (
            file.filename
        )

        current_document["text"] = text

        current_document["pages"] = (
            extraction["pages"]
        )

        current_document["extraction_method"] = (
            extraction["extraction_method"]
        )

        current_document["analysis"] = analysis

        # ----------------------------------------------------
        # RESPONSE
        # ----------------------------------------------------

        return {

            "status": "success",

            "filename": file.filename,

            "pages": extraction["pages"],

            "extraction_method":
                extraction["extraction_method"],

            "analysis": analysis,

            "message": (
                "Document processed, analyzed "
                "and stored for interaction."
            )
        }

    except HTTPException:

        raise

    except Exception as e:

        raise HTTPException(
            status_code=500,
            detail=(
                f"Analysis failed: {str(e)}"
            )
        )


# ============================================================
# ASK QUESTION ABOUT CURRENT DOCUMENT
# ============================================================

@app.post("/documents/ask")
async def ask_document_question(
    request: DocumentQuestion
):

    question = request.question.strip()

    if not question:

        raise HTTPException(
            status_code=400,
            detail="Question cannot be empty."
        )

    # --------------------------------------------------------
    # CHECK WHETHER DOCUMENT EXISTS
    # --------------------------------------------------------

    if not current_document["text"]:

        raise HTTPException(
            status_code=400,
            detail=(
                "No document has been analyzed yet. "
                "Upload and analyze a document first."
            )
        )

    document_text = current_document["text"]

    question_lower = question.lower()

    lines = [
        line.strip()
        for line in document_text.splitlines()
        if line.strip()
    ]

    # --------------------------------------------------------
    # FIELD KEYWORDS
    # --------------------------------------------------------

    keyword_groups = {

        "date": [
            "date",
            "issued",
            "issue date",
            "issued on"
        ],

        "name": [
            "name",
            "student",
            "candidate"
        ],

        "organization": [
            "organization",
            "organisation",
            "company",
            "institution"
        ],

        "document_number": [
            "certificate number",
            "certificate no",
            "invoice number",
            "invoice no",
            "receipt number",
            "receipt no",
            "purchase order number",
            "purchase order no",
            "po number",
            "po no"
        ],

        "total": [
            "total",
            "amount",
            "payable",
            "grand total"
        ],

        "vendor": [
            "vendor",
            "supplier",
            "seller"
        ]
    }

    matches = []

    # --------------------------------------------------------
    # SEARCH FIELD-SPECIFIC EVIDENCE
    # --------------------------------------------------------

    for field, keywords in keyword_groups.items():

        if any(
            keyword in question_lower
            for keyword in keywords
        ):

            for line in lines:

                if any(
                    keyword in line.lower()
                    for keyword in keywords
                ):

                    matches.append({

                        "field": field,

                        "evidence_text": line
                    })

    # --------------------------------------------------------
    # REMOVE DUPLICATES
    # --------------------------------------------------------

    unique_matches = []

    seen = set()

    for match in matches:

        key = (
            match["field"],
            match["evidence_text"]
        )

        if key not in seen:

            seen.add(key)

            unique_matches.append(
                match
            )

    # --------------------------------------------------------
    # DIRECT EVIDENCE FOUND
    # --------------------------------------------------------

    if unique_matches:

        primary = unique_matches[0]

        return {

            "status": "success",

            "filename":
                current_document["filename"],

            "answer": (
                "Based on the uploaded document: "
                + primary["evidence_text"]
            ),

            "evidence": [
                {

                    "field": item["field"],

                    "evidence_text":
                        item["evidence_text"],

                    "source":
                        "Uploaded document"
                }

                for item in unique_matches[:5]
            ],

            "grounded": True,

            "message": (
                "Answer generated using evidence "
                "from the uploaded document."
            )
        }

    # --------------------------------------------------------
    # GENERAL KEYWORD SEARCH
    # --------------------------------------------------------

    question_words = [
        word

        for word in re.findall(
            r"[a-zA-Z0-9]+",
            question_lower
        )

        if len(word) > 3
    ]

    scored_lines = []

    for line in lines:

        line_lower = line.lower()

        score = sum(

            1

            for word in question_words

            if word in line_lower
        )

        if score > 0:

            scored_lines.append(
                (score, line)
            )

    scored_lines.sort(
        key=lambda item: item[0],
        reverse=True
    )

    # --------------------------------------------------------
    # GENERAL EVIDENCE FOUND
    # --------------------------------------------------------

    if scored_lines:

        best_lines = [
            line
            for _, line in scored_lines[:3]
        ]

        return {

            "status": "success",

            "filename":
                current_document["filename"],

            "answer": (
                "I found relevant information "
                "in the uploaded document."
            ),

            "evidence": [

                {

                    "field":
                        "document_context",

                    "evidence_text":
                        line,

                    "source":
                        "Uploaded document"
                }

                for line in best_lines
            ],

            "grounded": True,

            "message": (
                "The response is grounded in "
                "text found in the uploaded document."
            )
        }

    # --------------------------------------------------------
    # NO EVIDENCE
    #
    # IMPORTANT:
    # We don't invent an answer.
    # --------------------------------------------------------

    return {

        "status": "not_found",

        "filename":
            current_document["filename"],

        "answer": (
            "I could not find evidence in the "
            "uploaded document to answer this question."
        ),

        "evidence": [],

        "grounded": False,

        "message": (
            "No supporting evidence was found. "
            "The system does not guess information "
            "that is not present in the document."
        )
    }