import calendar
from datetime import datetime
import streamlit as st
from streamlit_option_menu import option_menu
import plotly.graph_objects as go

import database as db


# Settings
incomes = ["Lønn", "Annen inntekt"]
expenses = [
    "Lån hus",
    "Lån bil",
    "Mat",
    "Forsikringer",
    "Kommunale avgifter",
    "Diverse utgifter",
    "Sparing",
]

currency = "NOK"
page_title = "Inntekt og utgiftsposter"
page_icon = ":money_with_wings:"
layout = "centered"

#############################################

st.set_page_config(page_title=page_title, page_icon=page_icon, layout=layout)
st.title(page_title + " " + page_icon)


# Drop down values for selecting the period
year = [datetime.today().year, datetime.today().year + 1]
month = list(calendar.month_name[1:])

# --- DATABASE INTERFACE ---
def get_all_periods():
    items = db.fetch_all_periods()
    periods = [item["key"] for item in items]
    return periods


# Hide Streamlit style
hide_st_style = """
            <style>
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_st_style, unsafe_allow_html=True)

# Navigation menu
selected = option_menu(
    menu_title=None,
    options=["Legg inn data", "Datavisualisering"],
    icons=["pencil-fill", "bar-chart-fill"],  # https://icons.getbootstrap.com/
    orientation="horizontal",
)

# Input and save periods
if selected == "Legg inn data":
    st.header(f"Legg inn verdier som {currency}")
    with st.form("entry_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        col1.selectbox("Velg måned:", month, key="month")
        col1.selectbox("Velg år:", year, key="year")

        "---"
        with st.expander("Inntekt"):
            for income in incomes:
                st.number_input(
                    f"{income}:", min_value=0, format="%i", step=10, key=income
                )
        with st.expander("Utgifter"):
            for expense in expenses:
                st.number_input(
                    f"{expense}:", min_value=0, format="%i", step=10, key=expense
                )
        with st.expander("Kommentarer"):
            comment = st.text_area("", placeholder="Skriv inn kommentar her")

        "---"

        submitted = st.form_submit_button("Lagre data")
        if submitted:
            period = (
                str(st.session_state["year"]) + "_" + str(st.session_state["month"])
            )
            # dette er en dictionary. Husk key=income ovenfor
            incomes = {income: st.session_state[income] for income in incomes}
            expenses = {expense: st.session_state[expense] for expense in expenses}

            db.insert_period(period, incomes, expenses, comment)
            st.write("Data lagret!")

# Plot periods
if selected == "Datavisualisering":
    st.header("Datavisualisering")
    with st.form("saved_periods"):
        period = st.selectbox("Velg periode:", get_all_periods())
        submitted = st.form_submit_button("Plot periode")
        if submitted:
            # Get data from database
            period_data = db.get_period(period)
            comment = period_data.get("comment")
            expenses = period_data.get("expenses")
            incomes = period_data.get("incomes")

            # Create metrics
            total_income = sum(incomes.values())
            total_expense = sum(expenses.values())
            remaining_budget = total_income - total_expense
            col1, col2, col3 = st.columns(3)
            col1.metric("Totalt inntekter", f"{total_income} {currency}")
            col2.metric("Totalt utgifter", f"{total_expense} {currency}")
            col3.metric("Til overs", f"{remaining_budget} {currency}")
            st.text(f"Kommentar: {comment}")

            # Create sankey chart
            label = list(incomes.keys()) + ["Utgifter"] + list(expenses.keys())
            source = list(range(len(incomes))) + [len(incomes)] * len(expenses)
            target = [len(incomes)] * len(incomes) + [
                label.index(expense) for expense in expenses.keys()
            ]
            value = list(incomes.values()) + list(expenses.values())

            # Data to dict, dict to sankey
            link = dict(source=source, target=target, value=value)
            node = dict(label=label, pad=20, thickness=15, color="#DAF7A6")
            data = go.Sankey(link=link, node=node)

            # Plot it!
            fig = go.Figure(data)
            fig.update_layout(margin=dict(l=0, r=0, t=5, b=5))
            st.plotly_chart(fig, use_container_width=True)
