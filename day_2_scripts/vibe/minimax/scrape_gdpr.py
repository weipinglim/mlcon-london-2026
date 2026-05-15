#!/usr/bin/env python3
"""Scrape GDPR articles 20-25 and generate summaries using qwen3.5:4B via Ollama."""

import json
import requests
import ollama

OLLAMA_MODEL = "qwen3.5:4b"

ARTICLES = [
    {
        "article": "Art. 20",
        "url": "https://gdpr-info.eu/art-20-gdpr/",
        "full_article": """1. The data subject shall have the right to receive the personal data concerning him or her, which he or she has provided to a controller, in a structured, commonly used and machine-readable format and have the right to transmit those data to another controller without hindrance from the controller to which the personal data have been provided, where:
   (a) the processing is based on consent pursuant to point (a) of Article 6(1) or point (a) of Article 9(2) or on a contract pursuant to point (b) of Article 6(1); and
   (b) the processing is carried out by automated means.

2. In exercising his or her right to data portability pursuant to paragraph 1, the data subject shall have the right to have the personal data transmitted directly from one controller to another, where technically feasible.

3. The exercise of the right referred to in paragraph 1 of this Article shall be without prejudice to Article 17. That right shall not apply to processing necessary for the performance of a task carried out in the public interest or in the exercise of official authority vested in the controller.

4. The right referred to in paragraph 1 shall not adversely affect the rights and freedoms of others."""
    },
    {
        "article": "Art. 21",
        "url": "https://gdpr-info.eu/art-21-gdpr/",
        "full_article": """1. The data subject shall have the right to object, on grounds relating to his or her particular situation, at any time to processing of personal data concerning him or her which is based on point (e) or (f) of Article 6(1), including profiling based on those provisions. The controller shall no longer process the personal data unless the controller demonstrates compelling legitimate grounds for the processing which override the interests, rights and freedoms of the data subject or for the establishment, exercise or defence of legal claims.

2. Where personal data are processed for direct marketing purposes, the data subject shall have the right to object at any time to processing of personal data concerning him or her for such marketing, which includes profiling to the extent that it is related to such direct marketing.

3. Where the data subject objects to processing for direct marketing purposes, the personal data shall no longer be processed for such purposes.

4. At the latest at the time of the first communication with the data subject, the right referred to in paragraphs 1 and 2 shall be explicitly brought to the attention of the data subject and shall be presented clearly and separately from any other information.

5. In the context of the use of information society services, and notwithstanding Directive 2002/58/EC, the data subject may exercise his or her right to object by automated means using technical specifications.

6. Where personal data are processed for scientific or historical research purposes or statistical purposes pursuant to Article 89(1), the data subject, on grounds relating to his or her particular situation, shall have the right to object to processing of personal data concerning him or her, unless the processing is necessary for the performance of a task carried out for reasons of public interest."""
    },
    {
        "article": "Art. 22",
        "url": "https://gdpr-info.eu/art-22-gdpr/",
        "full_article": """1. The data subject shall have the right not to be subject to a decision based solely on automated processing, including profiling, which produces legal effects concerning him or her or similarly significantly affects him or her.

2. Paragraph 1 shall not apply if the decision:
   (a) is necessary for entering into, or performance of, a contract between the data subject and a data controller;
   (b) is authorised by Union or Member State law to which the controller is subject and which also lays down suitable measures to safeguard the data subject's rights and freedoms and legitimate interests; or
   (c) is based on the data subject's explicit consent.

3. In the cases referred to in points (a) and (c) of paragraph 2, the data controller shall implement suitable measures to safeguard the data subject's rights and freedoms and legitimate interests, at least the right to obtain human intervention on the part of the controller, to express his or her point of view and to contest the decision.

4. Decisions referred to in paragraph 2 shall not be based on special categories of personal data referred to in Article 9(1), unless point (a) or (g) of Article 9(2) applies and suitable measures to safeguard the data subject's rights and freedoms and legitimate interests are in place."""
    },
    {
        "article": "Art. 23",
        "url": "https://gdpr-info.eu/art-23-gdpr/",
        "full_article": """1. Union or Member State law to which the data controller or processor is subject may restrict by way of a legislative measure the scope of the obligations and rights provided for in Articles 12 to 22 and Article 34, as well as Article 5 in so far as its provisions correspond to the rights and obligations provided for in Articles 12 to 22, when such a restriction respects the essence of the fundamental rights and freedoms and is a necessary and proportionate measure in a democratic society to safeguard:
   (a) national security;
   (b) defence;
   (c) public security;
   (d) the prevention, investigation, detection or prosecution of criminal offences or the execution of criminal penalties, including the safeguarding against and the prevention of threats to public security;
   (e) other important objectives of general public interest of the Union or of a Member State, in particular an important economic or financial interest of the Union or of a Member State, including monetary, budgetary and taxation matters, public health and social security;
   (f) the protection of judicial independence and judicial proceedings;
   (g) the prevention, investigation, detection and prosecution of breaches of ethics for regulated professions;
   (h) a monitoring, inspection or regulatory function connected, even occasionally, to the exercise of official authority in the cases referred to in points (a) to (e) and (g);
   (i) the protection of the data subject or the rights and freedoms of others;
   (j) the enforcement of civil law claims.

2. In particular, any legislative measure referred to in paragraph 1 shall contain specific provisions at least, where relevant, as to:
   (a) the purposes of the processing or categories of processing;
   (b) the categories of personal data;
   (c) the scope of the restrictions introduced;
   (d) the safeguards to prevent abuse or unlawful access or transfer;
   (e) the specification of the controller or categories of controllers;
   (f) the storage periods and the applicable safeguards taking into account the nature, scope and purposes of the processing or categories of processing;
   (g) the risks to the rights and freedoms of data subjects; and
   (h) the right of data subjects to be informed about the restriction, unless that may be prejudicial to the purpose of the restriction."""
    },
    {
        "article": "Art. 24",
        "url": "https://gdpr-info.eu/art-24-gdpr/",
        "full_article": """1. Taking into account the nature, scope, context and purposes of processing as well as the risks of varying likelihood and severity for the rights and freedoms of natural persons, the controller shall implement appropriate technical and organisational measures to ensure and to be able to demonstrate that processing is performed in accordance with this Regulation. Those measures shall be reviewed and updated where necessary.

2. Where proportionate in relation to processing activities, the measures referred to in paragraph 1 shall include the implementation of appropriate data protection policies by the controller.

3. Adherence to approved codes of conduct as referred to in Article 40 or approved certification mechanisms as referred to in Article 42 may be used as an element by which to demonstrate compliance with the obligations of the controller."""
    },
    {
        "article": "Art. 25",
        "url": "https://gdpr-info.eu/art-25-gdpr/",
        "full_article": """1. Taking into account the state of the art, the cost of implementation and the nature, scope, context and purposes of processing as well as the risks of varying likelihood and severity for rights and freedoms of natural persons posed by the processing, the controller shall, both at the time of the determination of the means for processing and at the time of the processing itself, implement appropriate technical and organisational measures, such as pseudonymisation, which are designed to implement data-protection principles, such as data minimisation, in an effective manner and to integrate the necessary safeguards into the processing in order to meet the requirements of this Regulation and protect the rights of data subjects.

2. The controller shall implement appropriate technical and organisational measures for ensuring that, by default, only personal data which are necessary for each specific purpose of the processing are processed. That obligation applies to the amount of personal data collected, the extent of their processing, the period of their storage and their accessibility. In particular, such measures shall ensure that by default personal data are not made accessible without the individual's intervention to an indefinite number of natural persons.

3. An approved certification mechanism pursuant to Article 42 may be used as an element to demonstrate compliance with the requirements set out in paragraphs 1 and 2 of this Article."""
    },
]


def generate_summary(article_text: str) -> str:
    """Generate a summary using qwen3.5:4B via Ollama."""
    prompt = f"""You are a legal assistant summarizing GDPR articles. Provide a concise 2-3 sentence summary of this GDPR article that would help someone quickly understand its purpose and key requirements:

{article_text}

Summary:"""

    response = ollama.generate(
        model=OLLAMA_MODEL,
        prompt=prompt,
        options={
            "temperature": 0.3,
            "num_ctx": 8192,
            "think": False,
        }
    )
    return response["response"].strip()


def main():
    gdpr_data = {"GDPR": []}

    for article in ARTICLES:
        print(f"Generating summary for {article['article']}...")
        summary = generate_summary(article["full_article"])

        gdpr_data["GDPR"].append({
            "article": article["article"],
            "summary": summary,
            "full_article": article["full_article"]
        })
        print(f"  ✓ {article['article']}: {summary[:80]}...")

    # Save to JSON file
    output_path = "day_2_scripts/vibe/minimax/gdpr_articles.json"
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(gdpr_data, f, indent=2, ensure_ascii=False)

    print(f"\nSaved {len(gdpr_data['GDPR'])} articles to {output_path}")
    return output_path


if __name__ == "__main__":
    main()