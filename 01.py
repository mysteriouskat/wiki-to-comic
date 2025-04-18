import re
import wikipedia
import urllib.parse
import sys
from google import genai
from google.genai import types

# ---- SETTINGS ----
client = genai.Client(api_key="")

# ---- STEP 1: FETCH WIKIPEDIA ARTICLE ----
def extract_title_from_url(url):
    try:
        if "/wiki/" not in url:
            raise ValueError("Invalid Wikipedia URL.")
        raw_title = url.split("/wiki/")[-1]
        return urllib.parse.unquote(raw_title).replace("_", " ")
    except Exception as e:
        return f"Error: Could not extract title - {e}"

def fetch_wikipedia_article_by_link(url, sentences=25):
    try:
        title = extract_title_from_url(url)
        wikipedia.set_lang("en")
        summary = wikipedia.summary(title, sentences=sentences, auto_suggest=False)
        return summary
    except wikipedia.exceptions.DisambiguationError as e:
        return f"Topic is ambiguous. Try one of these: {e.options[:5]}"
    except wikipedia.exceptions.PageError:
        return f"No Wikipedia page found for URL: {url}"
    except Exception as e:
        return f"An error occurred: {str(e)}"

# ---- STEP 2: CONVERT SUMMARY TO COMIC SCRIPT USING GEMINI ----
def generate_comic_script_with_gemini(summary_text, style="manga", complexity=2):
    complexity_description = {
        1: "Explain it like the reader is 5 years old – very simple language and concepts.",
        2: "Explain for general audience – accessible and clear.",
        3: "Include technical and complex details – for an advanced or academic reader."
    }
    explanation = complexity_description.get(complexity, complexity_description[2])

    prompt = f"""
    Transform the following educational summary into a {style}-style comic strip script.
    Use the following explanation level:
    {explanation}

    Break it into comic scenes with:
    - Visual description (should include where the speech bubble and text boxes are in the scene and their numbers, and also who speaks it)
    - Dialogue (speech bubbles)
    - Narration (text boxes)

    Enclose the beginning and end of the manuscript with [Manuscript Start] and [Manuscript End] respectively.
    don't use characters for markdown, just plain text.
    Use the following format:
    - Prefix Dialogue with "#D" and Narration with "#N" and visual description with "#V"
    - separate each scene with "---"
    - each scene should have a title like "Scene 1", "Scene 2", etc.
    - Include a title for the comic strip at the top.
    - A dialogue with #D, should include who is speaking the dialog, for ex. #D: "Character 1: Hello!"

    Summary:
    {summary_text}

    Comic Manuscript:
    """

    response = client.models.generate_content(
        model="gemini-1.5-pro-latest",
        contents=prompt,
        config=types.GenerateContentConfig(
            response_modalities=['Text']
        )
    )

    full_response = response.candidates[0].content.parts[0].text

    match = re.search(r"\[Manuscript Start\](.*?)\[Manuscript End\]", full_response, re.DOTALL)
    if match:
        return match.group(1).strip()
    else:
        print("Could not find manuscript tags. Returning full response.")
        return full_response.strip()

# ---- STEP 3: SAVE TO FILES ----
def save_to_file(text, filename="comic_manuscript.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)
    print(f"[✓] Manuscript saved to '{filename}'")

def save_metadata(style, complexity, filename="comic_metadata.txt"):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(f"Art Style: {style}\n")
        f.write(f"Complexity Level: {complexity}\n")
    print(f"[✓] Metadata saved to '{filename}'")

# ---- MAIN FUNCTION ----
def main():
    if len(sys.argv) != 4:
        print("Usage: python 01.py <Wikipedia URL> <Art Style> <Complexity Level>")
        sys.exit(1)

    wiki_url = sys.argv[1]
    art_style = sys.argv[2]
    try:
        complexity = int(sys.argv[3])
    except ValueError:
        print("Complexity must be an integer (1/2/3).")
        sys.exit(1)

    print("\nFetching article...")
    summary = fetch_wikipedia_article_by_link(wiki_url)
    if summary.startswith("An error") or summary.startswith("No Wikipedia") or summary.startswith("Topic"):
        print(summary)
        return

    print("\nGenerating comic manuscript...")
    manuscript = generate_comic_script_with_gemini(summary, art_style, complexity)
    print(manuscript)

    print("\n--- COMIC MANUSCRIPT PREVIEW ---\n")
    print(manuscript[:1000] + "...\n")  # Preview first 1000 chars

    save_to_file(manuscript)
    save_metadata(art_style, complexity)

if __name__ == "__main__":
    main()
