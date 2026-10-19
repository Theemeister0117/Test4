# app.py — Photo-to-Video + Undress (Adult / Uncensored capable)
import streamlit as st
import replicate
import requests
import tempfile
import os
from PIL import Image

st.set_page_config(
    page_title="Photo to Video / Undress",
    page_icon="🎬",
    layout="centered"
)

st.title("🎬 Photo to Video + Undress Generator")
st.caption(
    "Upload a photo of an adult woman. Animate her, undress her, or create explicit scenes "
    "(including adding male partners). Use an uncensored / Spicy endpoint for best results. "
    "Identity is locked primarily by the starting image."
)

with st.sidebar:
    st.header("Configuration")
    api_token = st.text_input("API Token (Replicate or other)", type="password")

    provider = st.selectbox(
        "Provider / Style",
        [
            "Replicate (Wan / Kling – often filtered)",
            "Uncensored / Spicy hosted (Wan Spicy, MiniMax H3 Spicy, Seedance Spicy, etc.)",
            "Local / self-hosted (best for zero filter)"
        ],
        index=1
    )

    model = st.text_input(
        "Model ID or endpoint",
        value="wavespeedai/wan-2.1-i2v-720p",
        help="For uncensored use the Spicy / unrestricted variant of the model"
    )

    mode = st.radio(
        "Generation Mode",
        ["Image → Video (animate)", "Undress Photo (Image → Image)"],
        index=0
    )

    duration = st.slider(
        "Approximate duration (seconds)",
        4, 15, 6,
        disabled=(mode != "Image → Video (animate)")
    )

    st.markdown("---")
    st.info(
        "**Best results tips**\n"
        "- Clear full-body or upper-body photo of an adult woman\n"
        "- Describe only the action / clothing change in the prompt\n"
        "- For sex scenes: mention the male partner, positions, camera, lighting\n"
        "- Use an uncensored endpoint when generating explicit content"
    )

if not api_token:
    st.warning("Enter your API token to continue.")
    st.stop()

os.environ["REPLICATE_API_TOKEN"] = api_token

uploaded_file = st.file_uploader(
    "Upload photo of the adult woman",
    type=["jpg", "jpeg", "png", "webp"]
)

if mode == "Image → Video (animate)":
    prompt_placeholder = (
        "Example (explicit):\n"
        "She slowly removes her clothes, then a muscular man enters the frame, "
        "kisses her, lifts her onto the bed and starts having passionate sex with her. "
        "Realistic skin, natural body movement, soft lighting, camera slowly circles around them."
    )
    default_negative = (
        "blurry, distorted face, deformed body, extra limbs, low quality, cartoon, "
        "text, watermark, child, underage, minor, young, teenager"
    )
else:
    prompt_placeholder = (
        "Example (undress):\n"
        "Completely remove all of her clothing. She is now fully nude, natural breasts and body, "
        "realistic skin texture, same pose and identity, high detail, soft lighting."
    )
    default_negative = (
        "clothes, clothing, underwear, bra, panties, shirt, pants, "
        "blurry, distorted face, deformed body, extra limbs, low quality, cartoon, "
        "text, watermark, child, underage, minor, young, teenager"
    )

prompt = st.text_area(
    "Prompt (be as explicit as you want)",
    height=140,
    placeholder=prompt_placeholder
)

negative = st.text_input("Negative prompt", value=default_negative)

st.markdown("**Quick prompt starters**")
col1, col2, col3 = st.columns(3)

with col1:
    if st.button("Undress fully"):
        st.session_state.prompt = (
            "Completely remove all of her clothing. She is now fully nude, "
            "realistic skin, natural body, same pose and identity, high detail."
        )
with col2:
    if st.button("Add male partner + sex"):
        st.session_state.prompt = (
            "A fit muscular man enters the scene, passionately kisses her, "
            "then has intense sex with her. Realistic bodies, natural movement, "
            "detailed skin, soft cinematic lighting, camera slowly moves around them."
        )
with col3:
    if st.button("Slow striptease"):
        st.session_state.prompt = (
            "She slowly and seductively removes her clothes one by one, "
            "looking at the camera, until she is completely nude. "
            "Natural body movement, realistic skin, soft lighting."
        )

if "prompt" in st.session_state:
    prompt = st.session_state.prompt

prompt = st.text_area(
    "Prompt (be as explicit as you want)",
    value=prompt,
    height=140,
    key="prompt_final"
)

if st.button("Generate", type="primary"):
    if not uploaded_file or not prompt.strip():
        st.error("Photo and prompt are required.")
    else:
        with st.spinner("Generating… (30–120 seconds typical)"):
            try:
                image = Image.open(uploaded_file).convert("RGB")
                with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as tmp:
                    image.save(tmp.name, format="PNG")
                    img_path = tmp.name

                input_payload = {
                    "image": open(img_path, "rb"),
                    "prompt": prompt,
                    "negative_prompt": negative,
                }

                if mode == "Image → Video (animate)" and (
                    "wan" in model.lower() or "kling" in model.lower() or "i2v" in model.lower()
                ):
                    input_payload["duration"] = duration

                output = replicate.run(model, input=input_payload)

                os.unlink(img_path)

                if isinstance(output, (list, tuple)):
                    result_url = output[0]
                elif hasattr(output, "url"):
                    result_url = output.url
                else:
                    result_url = str(output)

                st.success("Done!")

                if mode == "Image → Video (animate)":
                    st.video(result_url)
                    video_bytes = requests.get(result_url).content
                    st.download_button("Download MP4", video_bytes, "output.mp4", "video/mp4")
                else:
                    st.image(result_url, caption="Undressed result")
                    img_bytes = requests.get(result_url).content
                    st.download_button("Download Image", img_bytes, "undressed.png", "image/png")

            except Exception as e:
                st.error(f"Failed: {e}")
                st.info(
                    "Common causes:\n"
                    "- Content filter on the chosen endpoint (switch to a Spicy / uncensored model)\n"
                    "- Rate limit or invalid model ID\n"
                    "- Model does not support the requested mode (try a different endpoint)"
                )
