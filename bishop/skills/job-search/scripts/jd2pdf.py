"""Capture a LinkedIn job posting verbatim and render it to PDF.

Used by the job-search digest's JD capture check. The text is taken verbatim
from LinkedIn's guest posting API; nothing is paraphrased or summarised.

Part of Bishop, a free job-search plugin for Claude Code.
By Adam Hilliard - https://linkedin.com/in/adamhilliard - MIT licensed.
"""
import sys, re, html, urllib.request
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

sys.stdout.reconfigure(encoding="utf-8", errors="replace")


def fetch(jid):
    url = "https://www.linkedin.com/jobs-guest/jobs/api/jobPosting/%s" % jid
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    return urllib.request.urlopen(req, timeout=30).read().decode("utf8", "ignore")


def description_block(page):
    """Return only the posting's own description markup."""
    m = re.search(r'<div class="[^"]*show-more-less-html__markup[^"]*"[^>]*>(.*?)</div>',
                  page, re.S)
    if not m:
        m = re.search(r'<div class="[^"]*description__text[^"]*"[^>]*>(.*?)</section>',
                      page, re.S)
    if not m:
        raise SystemExit("no description block found")
    return m.group(1)


def to_lines(markup):
    t = markup
    t = re.sub(r"<br\s*/?>", "\n", t, flags=re.I)
    t = re.sub(r"</(p|li|ul|ol|h\d|div)>", "\n", t, flags=re.I)
    t = re.sub(r"<li[^>]*>", "• ", t, flags=re.I)
    t = re.sub(r"<[^>]+>", "", t)
    t = html.unescape(t)
    t = t.replace("\r", "")
    t = re.sub(r"[ \t]+", " ", t)
    t = re.sub(r"\n{3,}", "\n\n", t)
    return [ln.strip() for ln in t.split("\n")]


def build(jid, out_path, title_line, source_line):
    page = fetch(jid)
    lines = to_lines(description_block(page))

    styles = getSampleStyleSheet()
    body = ParagraphStyle("body", parent=styles["Normal"], fontSize=9.5,
                          leading=13, spaceAfter=5)
    head = ParagraphStyle("head", parent=styles["Title"], fontSize=15, leading=19)
    meta = ParagraphStyle("meta", parent=styles["Normal"], fontSize=8,
                          leading=11, textColor="#555555", spaceAfter=3)

    doc = SimpleDocTemplate(out_path, pagesize=letter,
                            leftMargin=0.85 * inch, rightMargin=0.85 * inch,
                            topMargin=0.75 * inch, bottomMargin=0.75 * inch,
                            title=title_line)
    story = [Paragraph(html.escape(title_line), head), Spacer(1, 4)]
    for s in source_line:
        story.append(Paragraph(html.escape(s), meta))
    story.append(Spacer(1, 10))
    for ln in lines:
        if ln:
            story.append(Paragraph(html.escape(ln), body))
    doc.build(story)
    print("wrote %s (%d text lines)" % (out_path, len([x for x in lines if x])))


if __name__ == "__main__":
    if len(sys.argv) < 4:
        sys.exit("usage: python jd2pdf.py <job-id> <out.pdf> <title> [source-line ...]")
    jid, out, title = sys.argv[1], sys.argv[2], sys.argv[3]
    build(jid, out, title, sys.argv[4:])
