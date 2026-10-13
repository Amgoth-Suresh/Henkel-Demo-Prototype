"""Regenerate the fictional technical data sheets: python make_samples.py"""

from pathlib import Path

from reportlab.lib.colors import HexColor, white
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

OUT = Path(__file__).parent / "samples"
OUT.mkdir(exist_ok=True)
WIDTH, HEIGHT = A4
NAVY = HexColor("#20364E")
BLUE = HexColor("#176A94")
GREY = HexColor("#58677A")

DOCUMENTS = [
    {
        "file": "01_BondFlex_A120_TDS.pdf", "title": "BondFlex A120", "code": "BFA-120",
        "category": "Two-component industrial adhesive", "pages": 4,
        "summary": [
            "BondFlex A120 is a fictional adhesive for demonstration purposes.",
            "Intended for rigid assembly where bond strength and working time matter.",
            "Values below represent sample lab readings, not a commercial specification.",
        ],
        "inline": [
            "Viscosity: 12500 mPa.s; Test method: ISO 2555; Conditions: 25 C; Substrate: n/a",
            "Density: 1.08 g/cm3; Test method: ISO 2811-1; Conditions: 23 C; Substrate: n/a",
            "Lap shear strength: 15 MPa; Test method: ISO 4587; Conditions: 7 d; Substrate: aluminium",
        ],
        "rows": [
            ("Open time", "12 min", "Internal OT-01", "23 C, 50% RH", "n/a"),
            ("Working life", "18 min", "Internal WL-02", "23 C", "n/a"),
            ("Tensile strength", "21 MPa", "ISO 527", "7 d after mix", "moulded sample"),
            ("Peak exotherm", "68 C", "Internal TC-03", "100 g mix", "n/a"),
        ],
        "chart_title": "Lap shear strength during cure", "x_label": "Cure time (days)",
        "y_label": "Lap shear strength (MPa)", "points": [(0, 0), (1, 3.5), (2, 7.1), (3, 10.2), (5, 13.6), (7, 15.0)],
        "comment": "Viscosity refers here to dynamic viscosity measured with a rotational instrument.",
    },
    {
        "file": "02_SealPro_S45_TDS.pdf", "title": "SealPro S45", "code": "SPS-045",
        "category": "Silicone sealing compound", "pages": 3,
        "summary": [
            "SealPro S45 is a fictional single-component sealant.",
            "This document intentionally varies terminology and units across sections.",
            "The specification is fictional and intended only for extraction practice.",
        ],
        "inline": [
            "Dynamic viscosity: 18000 cP; Test method: ASTM D2196; Conditions: 25 C; Substrate: n/a",
            "Density: 1.22 g/mL; Test method: ISO 2811-1; Conditions: 23 C; Substrate: n/a",
            "Shore A hardness: 28 points; Test method: ISO 868; Conditions: 7 d; Substrate: cured sheet",
        ],
        "rows": [
            ("Elongation @ break", "350 %", "ISO 37", "23 C; cured 7 d", "dumbbell"),
            ("Tensile resistance", "2.2 MPa", "ISO 37", "23 C", "cured sample"),
            ("Skin formation", "14 minutes", "Lab SM-07", "23 C / 50% RH", "n/a"),
            ("Curing speed", "3 mm / 24 h", "Lab CS-01", "23 C / 50% RH", "n/a"),
        ],
        "chart_title": "Cure depth versus elapsed time", "x_label": "Time (hours)",
        "y_label": "Cure depth (mm)", "points": [(0, 0), (6, 0.8), (12, 1.5), (18, 2.4), (24, 3.1), (30, 3.7)],
        "comment": "Some labels, like tensile resistance, may need expert mapping to a standard ontology.",
    },
    {
        "file": "03_CoataShield_C80_TDS.pdf", "title": "CoataShield C80", "code": "CSC-080",
        "category": "Protective industrial coating", "pages": 4,
        "summary": [
            "CoataShield C80 is a fictional protective coating used in this demo.",
            "The document intentionally contains a different kind of viscosity.",
            "Comparing viscosity values without considering methods and conditions is unsafe.",
        ],
        "inline": [
            "Kinematic viscosity: 520 mm2/s; Test method: ISO 3104; Conditions: 40 C; Substrate: n/a",
            "Solids content: 68 %; Test method: ISO 3251; Conditions: 105 C; Substrate: wet coating",
            "Dry film thickness: 120 um; Test method: ISO 2808; Conditions: 7 d; Substrate: steel",
        ],
        "rows": [
            ("Touch dry time", "25 min", "ASTM D1640", "23 C / 50% RH", "steel"),
            ("Viscosity, flow cup", "88 s", "ISO 2431", "23 C, cup 4", "n/a"),
            ("Pencil hardness", "3H", "ISO 15184", "7 d", "steel"),
            ("Gloss (60 degrees)", "82 GU", "ISO 2813", "23 C", "coated panel"),
        ],
        "chart_title": "Kinematic viscosity versus temperature", "x_label": "Temperature (C)",
        "y_label": "Kinematic viscosity (mm2/s)", "points": [(20, 910), (30, 700), (40, 520), (50, 390), (60, 300), (70, 235)],
        "comment": "Dynamic viscosity, kinematic viscosity and flow-cup time are not interchangeable.",
    },
]


def lines(c: canvas.Canvas, items: list[str], top: float, font_size: int = 10):
    c.setFont("Helvetica", font_size)
    c.setFillColor(NAVY)
    y = top
    for line in items:
        c.drawString(52, y, line)
        y -= 26
    return y


def new_page(c, doc, page_number):
    c.setFillColor(NAVY)
    c.rect(0, HEIGHT - 78, WIDTH, 78, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 18)
    c.drawString(52, HEIGHT - 45, doc["title"] + " | Technical Data Sheet")
    c.setFillColor(GREY)
    c.setFont("Helvetica", 9)
    c.drawString(52, 43, "FICTIONAL SAMPLE - NOT A HENKEL PRODUCT - FOR PORTFOLIO DEMO ONLY")
    c.drawRightString(WIDTH - 52, 43, f"Page {page_number} / {doc['pages']}")


def section(c, label, y):
    c.setFillColor(BLUE)
    c.setFont("Helvetica-Bold", 12)
    c.drawString(52, y, label)
    return y - 26


def chart(c, doc, top):
    title = doc["chart_title"]
    y = section(c, title, top)
    x0, y0 = 105, y - 340
    w, h = 370, 275
    pts = doc["points"]
    xmin, xmax = pts[0][0], pts[-1][0]
    ymin = 0
    ymax = max(y for _, y in pts) * 1.15
    c.setLineWidth(1)
    c.setStrokeColor(GREY)
    c.line(x0, y0, x0, y0 + h)
    c.line(x0, y0, x0 + w, y0)
    c.setFont("Helvetica", 8)
    for i in range(6):
        xv = xmin + (xmax - xmin) * i / 5
        xx = x0 + i * w / 5
        c.setFillColor(GREY)
        c.drawCentredString(xx, y0 - 16, f"{xv:g}")
        yv = ymin + (ymax - ymin) * i / 5
        yy = y0 + i * h / 5
        c.drawRightString(x0 - 12, yy - 3, f"{yv:.0f}")
        c.setStrokeColor(HexColor("#E2E7EB"))
        c.line(x0, yy, x0 + w, yy)

    c.setStrokeColor(BLUE)
    c.setFillColor(BLUE)
    c.setLineWidth(2.5)
    coords = [(x0 + (x - xmin) / (xmax - xmin) * w,
               y0 + (y - ymin) / (ymax - ymin) * h) for x, y in pts]
    for (ax, ay), (bx, by) in zip(coords, coords[1:]):
        c.line(ax, ay, bx, by)
    for x, y in coords:
        c.circle(x, y, 3, fill=1, stroke=0)
    c.setFillColor(NAVY)
    c.setFont("Helvetica", 10)
    c.drawCentredString(x0 + w/2, y0 - 42, doc["x_label"])
    c.saveState()
    c.translate(52, y0 + h/2)
    c.rotate(90)
    c.drawCentredString(0, 0, doc["y_label"])
    c.restoreState()
    lines(c, ["The curve is plotted as a picture; exact point values are not listed in a table.",
              "Any numerical values read from the plot are visual estimates."], y0 - 90, 9)


def generate(doc):
    c = canvas.Canvas(str(OUT / doc["file"]), pagesize=A4)
    c.setTitle(doc["title"] + " - fictional technical data sheet")
    new_page(c, doc, 1)
    y = section(c, "General product information", HEIGHT - 118)
    y = lines(c, [f"Product name: {doc['title']}", f"Product code: {doc['code']}",
                  "Manufacturer: Example Materials Lab (fictional)",
                  f"Category: {doc['category']}"], y)
    y -= 12
    y = section(c, "Product description", y)
    y = lines(c, doc["summary"], y, 10)
    y -= 10
    y = section(c, "Selected technical properties (narrative format)", y)
    y = lines(c, doc["inline"], y, 9)
    y -= 8
    section(c, "Important", y)
    lines(c, ["These selected values have explicit names, units, methods and test conditions.",
              "Other information uses tables or plots on later pages."], y - 28, 9)
    c.showPage()

    new_page(c, doc, 2)
    y = section(c, "Additional technical performance results", HEIGHT - 118)
    c.setFont("Helvetica", 9)
    c.setFillColor(GREY)
    c.drawString(52, y, "Values and units appear together. Methods and substrate differ by test.")
    y -= 42
    widths = [125, 85, 96, 120, 85]
    xs = [52]
    for width in widths:
        xs.append(xs[-1] + width)
    headers = ["Parameter", "Reported", "Test method", "Conditions", "Substrate"]
    c.setFillColor(NAVY)
    c.rect(52, y - 11, sum(widths), 28, stroke=0, fill=1)
    c.setFillColor(white)
    c.setFont("Helvetica-Bold", 8)
    for i, header in enumerate(headers):
        c.drawString(xs[i] + 5, y, header)
    for ridx, row in enumerate(doc["rows"]):
        yy = y - 35 - 39 * ridx
        c.setFillColor(HexColor("#F0F4F6") if ridx % 2 == 0 else white)
        c.rect(52, yy - 14, sum(widths), 38, stroke=0, fill=1)
        c.setFillColor(NAVY)
        c.setFont("Helvetica", 8)
        for i, value in enumerate(row):
            c.drawString(xs[i] + 5, yy, value)
    lines(c, ["Note: Different parameter labels may require review by material scientists.",
              doc["comment"]], y - 245, 9)
    c.showPage()

    new_page(c, doc, 3)
    chart(c, doc, HEIGHT - 118)
    c.showPage()

    if doc["pages"] == 4:
        new_page(c, doc, 4)
        y = section(c, "Interpretation and data governance", HEIGHT - 118)
        lines(c, [
            "Do not compare measurements unless the physical quantity is the same.",
            "Test method, material condition and substrate affect comparability.",
            "Unit conversions should only be done for physically equivalent properties.",
            "Unclear synonyms should be reviewed and approved by a domain expert.",
        ], y)
        y = section(c, "Use and handling (illustrative only)", y - 155)
        lines(c, [
            "Store in a dry environment, away from direct sunlight.",
            "Refer to actual supplier documentation for any real-world application.",
            "All numbers and products in this sheet are fabricated for demonstration.",
        ], y)
        c.showPage()
    c.save()
    print(OUT / doc["file"])


if __name__ == "__main__":
    for d in DOCUMENTS:
        generate(d)
