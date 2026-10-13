"""Two small PDF extractors: predictable regex, or a cloud LLM."""

import json
import re
from typing import Any

import fitz  # PyMuPDF
from pydantic import BaseModel, Field, field_validator


class Property(BaseModel):
    name: str
    value: float | None = None
    unit: str | None = None
    test_method: str | None = None
    conditions: str | None = None
    substrate: str | None = None
    source_page: int | None = None


class GraphPoint(BaseModel):
    x: float
    y: float


class Graph(BaseModel):
    title: str
    x_label: str | None = None
    y_label: str | None = None
    points: list[GraphPoint] = Field(default_factory=list)
    source_page: int | None = None


class Result(BaseModel):
    product_name: str | None = None
    product_code: str | None = None
    manufacturer: str | None = None
    category: str | None = None
    properties: list[Property] = Field(default_factory=list)
    graphs: list[Graph] = Field(default_factory=list)
    notes: list[str] = Field(default_factory=list)

    @field_validator("notes", mode="before")
    @classmethod
    def normalize_notes(cls, value: Any) -> Any:
        if value is None:
            return []
        if isinstance(value, str):
            return [value]
        return value


def read_pdf(pdf_bytes: bytes) -> tuple[list[str], list[bytes]]:
    """Read selectable text and render each page for vision-enabled models."""
    with fitz.open(stream=pdf_bytes, filetype="pdf") as pdf:
        if len(pdf) > 5:
            raise ValueError("This demo supports up to 5 pages per PDF.")
        texts = [page.get_text(sort=True) for page in pdf]
        images = [page.get_pixmap(matrix=fitz.Matrix(1.4, 1.4), alpha=False)
                  .tobytes("jpeg", jpg_quality=75) for page in pdf]
    return texts, images


# The regex method is intentionally deterministic. It works on the demo's
# text-based 'Property: value; Test method: ...' lines, not arbitrary layouts.
PROPERTY_PATTERN = re.compile(
    r"(?m)^(?P<name>[A-Za-z][A-Za-z0-9 /()\-]+):\s*"
    r"(?P<value>[\d,.]+)\s+(?P<unit>[^;\n]+);\s*"
    r"Test method:\s*(?P<method>[^;\n]+);\s*"
    r"Conditions:\s*(?P<conditions>[^;\n]+);\s*"
    r"Substrate:\s*(?P<substrate>[^\n]+)$"
)


def python_extract(page_texts: list[str]) -> Result:
    full_text = "\n".join(page_texts)
    fields = {
        "product_name": r"(?m)^Product name:\s*(.+)$",
        "product_code": r"(?m)^Product code:\s*(.+)$",
        "manufacturer": r"(?m)^Manufacturer:\s*(.+)$",
        "category": r"(?m)^Category:\s*(.+)$",
    }
    data = {}
    for field, pattern in fields.items():
        match = re.search(pattern, full_text)
        data[field] = match.group(1).strip() if match else None

    properties = []
    for page_number, text in enumerate(page_texts, start=1):
        for match in PROPERTY_PATTERN.finditer(text):
            properties.append(Property(
                name=match["name"].strip(),
                value=float(match["value"].replace(",", "")),
                unit=match["unit"].strip(),
                test_method=match["method"].strip(),
                conditions=match["conditions"].strip(),
                substrate=match["substrate"].strip(),
                source_page=page_number,
            ))
    return Result(
        **data, properties=properties,
        notes=[
            "Python mode uses regex: it only captures known text patterns.",
            "Tables with different layouts and plotted curves are not interpreted.",
            "Units and property names are preserved as written; no unsafe conversions.",
        ],
    )


SYSTEM_PROMPT = """You extract technical product data from PDF technical data sheets.
Return ONLY a JSON object with these exact top-level keys:
product_name, product_code, manufacturer, category, properties, graphs, notes.
Each properties element has: name, value (number or null), unit, test_method,
conditions, substrate, source_page (1-based integer or null).
Each graphs element has: title, x_label, y_label, source_page, points (list of {x,y}).

IMPORTANT:
- Extract technical properties AND metadata (units, method, testing conditions, substrate).
- Preserve original terminology and units. Do not assume similar-sounding properties
  are equivalent, or convert units without verified conversion and conditions.
- Distinguish dynamic viscosity from kinematic viscosity.
- If a field is absent, use null. Do not invent methods or conditions.
- If page images are included, visually inspect plotted graphs. You may record
  a SMALL number of approximate points only when a graph's axes and curve are clear.
  Label graph estimates as approximate in notes. Do not claim exact graph readings.
- If no images are provided, leave graphs empty; text alone cannot digitize a plot.
- Output valid JSON only, with numeric property values when clear.
"""


def _json_from_llm(text: str) -> dict:
    """Accept ordinary JSON and fenced JSON (some models add Markdown)."""
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = re.sub(r"^```(?:json)?\s*|\s*```$", "", cleaned).strip()
    return json.loads(cleaned)


def ai_extract(page_texts: list[str], page_images: list[bytes],
               model: str, api_key: str, use_vision: bool) -> Result:
    if not api_key.strip():
        raise ValueError("Enter your API key to use AI mode.")
    if not model.strip():
        raise ValueError("Enter a model name.")

    labeled_text = "\n\n".join(
        f"--- PAGE {i} ---\n{page}" for i, page in enumerate(page_texts, 1)
    )
    instruction = SYSTEM_PROMPT + "\n\nPDF TEXT:\n" + labeled_text[:60000]

    from google import genai
    from google.genai import types

    client = genai.Client(api_key=api_key)
    parts = [types.Part.from_text(text=instruction)]
    if use_vision:
        parts += [types.Part.from_bytes(data=image, mime_type="image/jpeg")
                  for image in page_images]
    response = client.models.generate_content(
        model=model,
        contents=parts,
        config=types.GenerateContentConfig(
            response_mime_type="application/json", temperature=0,
        )
    )
    if not response.text:
        raise ValueError("The model returned no text. Try a different model.")
    raw = response.text

    return Result.model_validate(_json_from_llm(raw))
