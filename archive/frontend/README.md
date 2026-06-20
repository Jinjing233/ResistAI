# Legacy frontend (design reference only)

These files are **not used at runtime**. The live application is powered entirely by **Streamlit** (`app.py`).

| File | Purpose |
|------|---------|
| `index.html` | Original static page layout reference |
| `script.js` | Original payload rendering logic (superseded by Python) |

Active UI styles live in `frontend/style.css`, which is still loaded by `app.py`.

Do not delete `frontend/style.css` from the project root `frontend/` folder.
