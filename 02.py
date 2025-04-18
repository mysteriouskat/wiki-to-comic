from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

# Initialize Gemini client
client = genai.Client(api_key="")

# Read comic metadata
with open('comic_metadata.txt', 'r') as meta_file:
    meta_data = meta_file.read().strip().splitlines()

# Extract Art Style and Complexity Level
art_style = meta_data[0].split(":")[1].strip().lower()  # 'western' or 'manga'
complexity_level = int(meta_data[1].split(":")[1].strip())  # 1, 2, or 3

# Read manuscript
with open('comic_manuscript.txt', 'r',encoding='utf-8') as manuscript_file:
    manuscript = manuscript_file.read()

# Split into scenes
scenes = manuscript.split('---')

# Function to create a combined page prompt
def create_page_prompt(scenes, art_style, complexity_level):
    panel_descriptions = []

    for idx, scene in enumerate(scenes, start=1):
        if not scene.strip():
            continue  # Skip empty scenes

        lines = scene.strip().splitlines()
        visual = dialogue = narration = ""

        for line in lines:
            if line.startswith("#V"):
                visual = line[2:].strip()
            elif line.startswith("#D"):
                dialogue += line[2:].strip() + " "
            elif line.startswith("#N"):
                narration += line[2:].strip() + " "

        panel_description = (
            f"Panel {idx}: Visual - {visual}. "
            f"Dialogue - '{dialogue.strip()}' "
            f"and Narration - '{narration.strip()}'."
        )
        panel_descriptions.append(panel_description)

    # Build complexity descriptor
    if complexity_level == 1:
        complexity_desc = "in a bright, colorful, playful, kid-friendly style with simple shapes and cheerful characters"
    elif complexity_level == 2:
        complexity_desc = "in a standard, balanced, general-audience style"
    else:
        complexity_desc = "in a detailed, advanced, mature, and realistic style"

    # Build art style descriptor
    if art_style == "western":
        art_style_desc = "in a full-color western comic book style"
    else:
        art_style_desc = "in a black and white ink manga style"

    # Final prompt construction
    prompt = (
        f"Create a complete comic page {art_style_desc}, {complexity_desc}. "
        f"The page should be divided into {len(panel_descriptions)} panels. "
        f"Each panel contains:\n"
        + "\n".join(panel_descriptions)
        + "\nThe dialogues should be in speech bubbles and narration should be in narration boxes, DO NOT generate any text in the image into the bubbles or boxes, leave them blank"
        f"Lay out the panels clearly on the page."
        f"Do not write any text in the image AT ALL"
    )

    return prompt

# Generate a prompt for the full page
page_prompt = create_page_prompt(scenes, art_style, complexity_level)

print(f"Generating Comic Page with prompt:\n{page_prompt}\n")

# Generate image
response = client.models.generate_content(
    model="gemini-2.0-flash-exp-image-generation",
    contents=page_prompt,
    config=types.GenerateContentConfig(
        response_modalities=['Text', 'Image']
    )
)

# Handle response
for part in response.candidates[0].content.parts:
    if part.text is not None:
        print("Text Response:", part.text)
    elif part.inline_data is not None:
        image = Image.open(BytesIO(part.inline_data.data))
        image.save('comic_page.png')
        # image.show()

print("Comic page generation complete!")
