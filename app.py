import streamlit as st
from tagging import _get_api_key, tag_product


def main():
    st.set_page_config(page_title="AI Product Tagging", page_icon="🔖")

    st.title("AI Product Tagging with OpenAI")
    st.write(
        "Enter one product per line. The app returns JSON with a category and brand "
        "chosen from your allowed list."
    )

    sample_products = "Aple iphne 15 pro max\nsamsng galaxy s24\nsony bravia 55 inch tv\nlenovo thinkpad laptop"
    products_text = st.text_area(
        "Products (one per line):",
        value=sample_products,
        height=150,
    )

    api_key = _get_api_key()
    if not api_key:
        st.error(
            "API key not found. Set `OPENAI_API_KEY` (recommended) or `OPEN_AI_API` in your `.env`."
        )
        st.stop()
    st.caption("API key detected from environment (.env). Requests are generated using your key.")

    if st.button("Generate Tags", type="primary"):
        products = [p.strip() for p in products_text.splitlines() if p.strip()]

        if not products:
            st.warning("Please enter at least one product.")
            return

        try:
            with st.spinner("Tagging..."):
                tagged = {p: tag_product(p) for p in products}
        except Exception as e:
            st.error(f"Error while generating tags: {e}")
            return

        st.subheader("Results")
        for product, obj in tagged.items():
            st.markdown(f"**Product:** {product}")
            st.json(obj)
            st.markdown("---")


if __name__ == "__main__":
    main()

