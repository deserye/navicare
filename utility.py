"""Password gate from the bootcamp Streamlit lesson.

The lesson stops the page with:

    from utility import check_password
    if not check_password():
        st.stop()

NaviCare keeps Home, About Us, and Methodology open. Call this only for the
journeys, Ask NaviCare, and the Admin page.
"""

from __future__ import annotations

import streamlit as st


def check_password() -> bool:
    """Return True when a user or admin is signed in. Otherwise show the form."""
    if st.session_state.get("auth_group") in {"User", "Admin"}:
        return True

    import app as navicare

    destination = st.session_state.get("after_login")
    if destination:
        intro = f"Sign in to open {destination}. Home, About Us, and Methodology stay open."
    else:
        intro = "Sign in to use Understand my scheme, Care conversation, and Ask NaviCare."
    st.markdown(
        f'<div class="hero"><div class="eyebrow">Educational prototype</div><h1>Sign in to NaviCare</h1><p>{intro}</p></div>',
        unsafe_allow_html=True,
    )
    with st.form("login_form"):
        username = st.text_input("Username", placeholder="user or admin")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Sign in", type="primary")
    st.caption("User: username `user`. Admin: username `admin`. Password: `aibootcamp`.")
    if st.button("Back to the open pages"):
        st.session_state["login_open"] = False
        st.session_state.pop("after_login", None)
        st.rerun()
    if submitted:
        group = navicare.authenticate(username, password)
        if group is None:
            st.error("That username or password does not match.")
        else:
            st.session_state["auth_user"] = username.strip().lower()
            st.session_state["auth_group"] = group
            st.session_state["login_open"] = False
            next_page = st.session_state.pop("after_login", None)
            st.session_state["pending_page"] = (
                next_page if next_page in navicare.pages_for(group) else "Home"
            )
            st.rerun()
    return False
