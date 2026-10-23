# Prepress AI Agent — online deployment starter

## Privacy first
- Do not use real VistaPrint/client artwork unless your employer explicitly approves Streamlit Community Cloud and the data-handling arrangement.
- A private app limits who can open the interface; it does not mean the code runs locally or that uploaded data never reaches the hosting provider.
- This code does not intentionally save uploaded files to disk or send them to an external AI API. Files are processed by the hosted app in memory; hosting-provider operations and policies still apply.
- Keep the GitHub repository private and set the Streamlit app to private. Invite only approved viewers. Never commit client artwork, credentials, or API keys.
- For employer-confidential files, use only company-approved hosting.

## What it checks
- PDF page size vs entered artboard + bleed.
- Approximate effective DPI for placed raster images.
- Possible white/uncovered edge gaps using a raster heuristic.
- Likely `/Separation` and `/DeviceN` PDF object definitions.
- Downloadable CSV report.

It does not automatically edit artwork or convert spot colors. Checks are heuristic and must be validated against known test PDFs.

## Deploy on Streamlit Community Cloud
1. Sign in to GitHub and create a **private** repository, e.g. `prepress-ai-agent`.
2. Upload all files in this folder to the repository root, preserving the `.streamlit` folder.
3. Visit https://share.streamlit.io and sign in with GitHub.
4. Choose **Create app**.
5. Select the repository, branch (`main` usually), and entrypoint `app.py`.
6. In **Advanced settings**, select a supported Python version. No secrets are required.
7. Click **Deploy** and wait for the build to finish.
8. In the app settings, open **Sharing** and select **Only specific people can view this app**. Invite only approved viewers.
9. Test access in a signed-out/incognito browser before sharing the URL.
10. Use only non-confidential PDFs until company approval is documented.

Official guides:
- Deploy: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/deploy
- Private sharing: https://docs.streamlit.io/deploy/streamlit-community-cloud/share-your-app
- Dependencies: https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/app-dependencies

## Update
Commit changes to the private GitHub repository; Community Cloud detects repository updates and redeploys. Never commit secrets or client artwork.
