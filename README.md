# NaviCare

**Full project title:** NaviCare: A CareShield Life and ElderShield Information Navigator

NaviCare is an educational Streamlit app for understanding Singapore’s CareShield Life, ElderShield, long-term-care claims, and caregiver-support pathways. It offers two guided journeys and an optional source-grounded chatbot. It does not check a real person’s coverage.

## Features

**Understand my long-term-care scheme** uses broad birth-year context, audience, and topic focus to generate learning prompts and a high-level comparison of CareShield Life, ElderShield, and supplements. Actual coverage has to be checked on CPF Board’s member site.

**Prepare for a care or claim conversation** uses broad audience, task, and intended destination to produce a preparation checklist. It links to CPF Board, MOH, and AIC. It does not assess disability, interpret medical reports, or predict claim approval.

**Ask NaviCare** answers follow-up questions from the same official-source notes. Those answers work with no API key. If `OPENAI_API_KEY` is set, the page uses a language model for the same kind of question and still tells the reader to verify the answer.

**Home**, **About Us**, and **Methodology** are open without a password. **Understand my scheme**, **Care conversation**, and **Ask NaviCare** ask the visitor to sign in. The user account opens those three. The admin account opens those three and an Admin page. Demo usernames are `user` and `admin`. The password for both is `aibootcamp`.

Illustrations are image files in [`assets/`](assets/), next to [`app.py`](app.py). Streamlit loads them from that folder.

## Important educational boundary

> This web application is a prototype developed for educational purposes only. The information provided here is NOT intended for real-world usage and should not be relied upon for making any decisions, especially those related to financial, legal, or healthcare matters.

The chatbot may generate inaccurate information. Do not enter diagnoses, medical records, NRIC details, account numbers, exact balances, addresses, or other identifying information. Always verify current information with CPF Board, MOH, or AIC.

## Run locally

From the project folder:

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python -m streamlit run app.py
```

On Windows Command Prompt, create and activate the environment with `py -m venv .venv` and `.venv\Scripts\activate.bat`, then use the same `python -m pip` and `python -m streamlit` commands. The app opens at `http://localhost:8501`.

Check the project before you deploy:

```bash
python test_app.py
python check_links.py
```

`check_links.py` requests every web link in the repo and confirms the illustration files exist.

## Optional chatbot

The guided pages work with no secrets. To enable Ask NaviCare, copy [`.streamlit/secrets.toml.example`](.streamlit/secrets.toml.example) to `.streamlit/secrets.toml` and replace the placeholder key:

```toml
OPENAI_API_KEY = "your-secret-key"
CARE_LLM_MODEL = "gpt-4o-mini"
```

You can also set those names as environment variables for one terminal session. Streamlit reads secrets from `.streamlit/secrets.toml`, not from a file in the project root. `.streamlit/secrets.toml` is gitignored.

The app defaults to `gpt-4o-mini` and uses standard chat-completion fields. If your account uses a different model, set `CARE_LLM_MODEL`. Set `OPENAI_API_BASE` only for an OpenAI-compatible endpoint.

If a previous copy of this project included a real API key, rotate that key. Put the new key only in Streamlit secrets or your local ignored secrets file.

## Sign-in

Home, About Us, and Methodology stay open. The two journeys and Ask NaviCare use these demo accounts:

| Group | Username | Password |
| --- | --- | --- |
| User | `user` | `aibootcamp` |
| Admin | `admin` | `aibootcamp` |

Put that password in the LaunchPad form with the Streamlit URL. To use a different password on the hosted app, set `USER_PASSWORD` and `ADMIN_PASSWORD` in Streamlit secrets. If those are unset, the app keeps `aibootcamp`.

## Bootcamp submission checklist

NaviCare is a learning prototype. Do not use it for a real financial, legal, or healthcare decision, do not promote it to the public, and do not collect real or sensitive user data.

What the app already includes:

- Two use cases: **Understand my scheme** and **Care conversation**, each with a form, a table or checklist, and a visual guide.
- Follow-up answers on **Ask NaviCare**, including when no model key is configured.
- The required disclaimer on **Home**, under “Important prototype notice”.
- **About Us** (scope, objectives, data sources, features) and **Methodology** (data flow, implementation, and a flowchart for each use case).
- Links only to public CPF Board, MOH, and AIC pages.
- Home, About Us, and Methodology open without a password. The two journeys and Ask NaviCare require `user` or `admin`. Admin also has an Admin page. The password is `aibootcamp`.

What you still submit yourself:

1. Deploy the app on [Streamlit Community Cloud](https://share.streamlit.io/) from your GitHub repository (`main`, main file `app.py`).
2. In LaunchPad, open the Ideate tab, edit the idea, and fill Proposed Solution with the title, a short description, the Streamlit URL, the password `aibootcamp`, the project type tag, and the team members.
3. Add `OPENAI_API_KEY` in **Settings → Secrets** only if you also want model answers.
4. Open the live URL. Check Home, About Us, and Methodology before signing in. Then sign in as `user` and as `admin` and check both journeys, Ask NaviCare, and the Admin page.

## Pictures

Every illustration the app shows is a file in `assets/`:

- `assets/navicare_logo_mark.jpg`
- `assets/navicare_hero.jpg`
- `assets/navicare_scheme.jpg`
- `assets/navicare_conversation.jpg`
- `assets/styles.css`

Keep each picture under 1.5 MB. GitHub rejects files over 100 MB, and large images slow Streamlit Community Cloud. To replace a drawing with your own photo, shrink it first. The script needs Pillow (`python -m pip install pillow`):

```bash
python scripts/optimize_assets.py \
  --hero /path/to/hero.jpg \
  --scheme /path/to/scheme.jpg \
  --conversation /path/to/conversation.jpg \
  --logo /path/to/logo.png
```

That writes `assets/navicare_hero.jpg`, `assets/navicare_scheme.jpg`, `assets/navicare_conversation.jpg`, and `assets/navicare_logo_mark.png`, each under 400 KB. A `.jpg` with the same name is used instead of the `.png`.

## Deploy on GitHub, then host on Streamlit

Streamlit Community Cloud runs the app from a GitHub repository. After the first connection, every push to the deployed branch updates the hosted app.

### 1. Put the project on GitHub

Create an empty repository on GitHub. Do not add a README, license, or `.gitignore` there, because this project already has them.

On your computer, from the unzipped `NaviCare` folder:

```bash
git init
git add .
git commit -m "Add NaviCare Streamlit app"
git branch -M main
git remote add origin <paste-the-repository-url>
git push -u origin main
```

Confirm these files are at the repository root, not inside an extra folder:

- `app.py`
- `requirements.txt`
- `assets/`

Do not commit `.streamlit/secrets.toml`. The example file `.streamlit/secrets.toml.example` is safe to commit.

### 2. Host it on Streamlit Community Cloud

1. Open [Streamlit Community Cloud](https://share.streamlit.io/) and sign in with the same GitHub account.
2. Choose **Create app**.
3. Select the new repository, the `main` branch, and `app.py` as the main file path.
4. Click **Deploy**. Streamlit installs `requirements.txt` and starts the app. The first deploy can take a few minutes.
5. Open the URL Streamlit shows. Check Home, both journeys, Ask NaviCare, About Us, and Methodology, and open each official-source button.

The guided pages work with no secrets. To turn on the chatbot, open the app’s **Settings → Secrets** and paste:

```toml
OPENAI_API_KEY = "your-secret-key"
CARE_LLM_MODEL = "gpt-4o-mini"
```

The sign-in password is already `aibootcamp` for `user` and `admin`. Add `OPENAI_API_KEY` only if you want model answers. Save. If the app does not reload, use **Manage app → Reboot**.

Later changes are deployed by pushing to `main`:

```bash
git add .
git commit -m "Update NaviCare"
git push
```

## Official sources

These public pages are linked from the app. Confirm anything current or personal on the official site:

- [CPF Board — CareShield Life](https://www.cpf.gov.sg/member/healthcare-financing/careshield-life)
- [CPF Board — ElderShield](https://www.cpf.gov.sg/member/healthcare-financing/eldershield)
- [MOH — CareShield Life](https://www.moh.gov.sg/managing-expenses/schemes-and-subsidies/careshield-life/careshield-life/)
- [MOH — CareShield Life and ElderShield Supplements](https://www.moh.gov.sg/managing-expenses/schemes-and-subsidies/careshield-life/careshield-life-and-eldershield-supplements/)
- [AIC — CareShield Life](https://www.aic.sg/Financial-Assistance/CareShield-Life)
- [CPF member home](https://www.cpf.gov.sg/member)

The illustrations are original visuals for this prototype. They do not imply CPF Board, MOH, or AIC endorsement.
