# # Pre-render python script that runs before being published
# # Currently used to generate references for Papers page from a .bib file!

import os

if not os.getenv("QUARTO_PROJECT_RENDER_ALL"):
  # only run when rendering project
  exit()

import bibtexparser
import calendar
import yaml 

def create_pub_listing(bib_file, author="Weaving, Tim"):
    """
    Converts a publication.bib to .yml this is used to build Table of papers in qmd file!
    All generated here.
    """
    with open(bib_file, "r", encoding="utf-8") as f:
        bib_database = bibtexparser.load(f)

    articles = []

    for entry in bib_database.entries:
        authors_raw = entry.get("author", "").replace("\n", " ")
        authors = [a.strip() for a in authors_raw.replace(" and ", ";").split(";")]

        try:
            position = authors.index(author) + 1
            position_str = f"{position}/{len(authors)}"
        except ValueError:
            position_str = "NA"

        # === Journal / path / date handling ===
        journal = entry.get("journal", "")
        path = None
        year = entry.get("year", "")

        if entry.get("archivePrefix", "").lower() == "arxiv" or entry.get("archiveprefix", "").lower() == "arxiv":
            # arXiv-only paper
            journal = "arXiv"
            path = entry.get("url")
            if not path and entry.get("eprint"):
                path = f"https://arxiv.org/abs/{entry['eprint']}"

            # Set date from eprint: YYMM.xxxxx → YYYY-MM
            eprint = entry.get("eprint", "")
            if eprint and len(eprint) >= 4:
                mm = int(eprint[2:4])
                month_num = str(mm).zfill(2)
        else:
            # Regular journal/booktitle papers
            # DOI takes precedence
            if entry.get("doi"):
                path = f"https://doi.org/{entry['doi']}"
            elif entry.get("url"):
                path = entry["url"]

            # Month normalization if provided
            month = entry.get("month", "").strip().lower()
            if month:
                month_map = {m.lower(): str(i).zfill(2) for i, m in enumerate(calendar.month_abbr) if m}
                month_map.update({m.lower(): str(i).zfill(2) for i, m in enumerate(calendar.month_name) if m})
                if month.isdigit():
                    month_num = str(int(month)).zfill(2)
                else:
                    month_num = month_map.get(month, "00")

        date = f"{year}-{month_num}"

        # === Title ===
        title = entry.get("title", "").replace("{", "").replace("}", "")

        # === Assemble dict ===
        article = {
            "title": title,
            "journal-title": f"*{journal}*",
            "date": date,
            "author-position": position_str,
        }
        if path:
            article["path"] = path

        articles.append(article)

    # Write publications.yml
    yml_file = bib_file.replace(".bib", ".yml")
    with open(yml_file, "w", encoding="utf-8") as f:
        yaml.safe_dump(articles, f, sort_keys=False, allow_unicode=True)

    # Write companion .qmd (unchanged)
    qmd_file = bib_file.replace(".bib", ".qmd")
    yaml_text = """---
title: 'Publications'
author:
  - name: Tim Weaving
    orcid: 0000-0003-3362-7275
    email: timothy.weaving.20@ucl.ac.uk
    affiliation:
      - name: University College London
        city: London
        country: United Kingdom
        url: "https://www.ucl.ac.uk"
title-block-banner: true
date-format: 'MMMM,<br>YYYY'
listing:
  contents:
    - publications.yml
  page-size: 10
  sort: 'date desc'
  type: table
  categories: false
  sort-ui: [date, title, journal-title, author-position]
  filter-ui: [date, title, journal-title]
  fields: [date, title, journal-title, author-position]
  field-display-names:
    date: Issued
    journal-title: Journal
    author-position: AuthorPos
---
"""
    with open(qmd_file, "w", encoding="utf-8") as f:
        f.write(yaml_text)

    print(f"Wrote {yml_file} and {qmd_file}")



if __name__ == '__main__':

  dirpath = os.path.dirname(os.path.realpath(__file__))
  papers_dir = os.path.join(dirpath, 'papers')

  bibfile_name = [f for f in os.listdir(papers_dir) if f.endswith(".bib")][0]
  bibfile_path = os.path.join(papers_dir, bibfile_name)
  assert os.path.isfile(bibfile_path), f"no bibtex file at {bibfile_path}"
  
  create_pub_listing(bibfile_path)


