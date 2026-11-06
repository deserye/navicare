import app

coverage = app.coverage_output(
    "Born in 1980 or after",
    "Claims and severe disability",
    "Family member or caregiver",
)
assert len(coverage["prompts"]) == 3
assert any("six activities of daily living" in item for item in coverage["prompts"])
assert any("AIC" in item for item in coverage["prompts"])

care = app.care_output(
    "Caregiver or family member",
    "Apply or find application support",
    "AIC",
)
assert len(care["checklist"]) == 5
assert any("eFASS" in item for item in care["checklist"])
assert any("mental capacity" in item for item in care["checklist"])

assert "IMPORTANT NOTICE" in app.DISCLAIMER
assert "CareShield Life" in app.SOURCE_CONTEXT
assert "ElderShield" in app.SOURCE_CONTEXT
assert "long-term-care" in app.SOURCE_CONTEXT

assert app.resolve_nav(None, None) == "Home"
assert app.resolve_nav("Home", "Care conversation") == "Care conversation"
assert app.resolve_nav("About Us", "Not a page") == "About Us"
assert app.resolve_nav(None, None, "Methodology") == "Methodology"
assert app.resolve_nav("Home", None, "Methodology") == "Home"
assert app.resolve_nav(None, None, "../secrets") == "Home"
assert app.resolve_nav(None, "Admin", None, app.pages_for("User")) == "Home"
assert app.pages_for(None) == app.PUBLIC_PAGES
assert "Understand my scheme" not in app.pages_for(None)
assert "About Us" in app.pages_for(None)
assert "Ask NaviCare" in app.pages_for("User")
assert "Admin" not in app.pages_for("User")
assert "Methodology" in app.pages_for("User")
assert app.pages_for("Admin")[-1] == "Admin"
assert app.authenticate("user", "aibootcamp") == "User"
assert app.authenticate(" Admin ", "aibootcamp") == "Admin"
assert app.authenticate("user", "wrong") is None
assert app.authenticate("guest", "aibootcamp") is None
assert app.DEFAULT_PASSWORD == "aibootcamp"

for destination in app.HOME_DESTINATIONS.values():
    assert destination in app.PAGES
for page in app.PAGES:
    assert page

seen_urls = set()
for source in app.OFFICIAL_SOURCES:
    assert source["url"].startswith("https://")
    assert source["url"] not in seen_urls
    seen_urls.add(source["url"])
    assert source["url"] in app.SOURCE_CONTEXT or source["key"] in {"moh", "cpf-member"}

assert app.STYLES_PATH.exists()
for stem in app.IMAGE_STEMS:
    picture = app.image_file(stem)
    assert picture is not None, stem
    assert picture.parent == app.ASSET_DIR
    assert 200 < picture.stat().st_size <= app.MAX_RASTER_BYTES, picture

original_get_secret = app.get_secret
app.get_secret = lambda name: ""
empty_reply = app.assistant_reply([])
assert "CareShield Life" in empty_reply
assert "Verify with CPF Board, MOH, or AIC" in empty_reply
adl_reply = app.assistant_reply(
    [{"role": "user", "content": "What are the six activities of daily living?"}]
)
assert "washing" in adl_reply.lower()
assert "transferring" in adl_reply.lower()
assert "Verify with CPF Board, MOH, or AIC" in adl_reply
apply_reply = app.assistant_reply(
    [{"role": "user", "content": "Where can a caregiver learn about applying?"}]
)
assert "eFASS" in apply_reply
assert "AIC" in apply_reply
app.get_secret = original_get_secret
print("NaviCare deterministic smoke tests passed.")
