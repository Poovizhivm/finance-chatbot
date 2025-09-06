import streamlit as st
import pandas as pd
from datetime import date, timedelta

st.set_page_config(page_title="💸 Finance Chatbot", page_icon="🤖")

st.title("🤖 AI-Powered Personal Finance Assistant")

# ===================== Session State =====================
if "expenses" not in st.session_state:
    st.session_state.expenses = pd.DataFrame(columns=["Date", "Category", "Amount", "Description"])

if "messages" not in st.session_state:
    st.session_state.messages = []  # chat history

if "last_category" not in st.session_state:
    st.session_state.last_category = None

# ===================== Add Expense Section =====================
st.subheader("➕ Add a New Expense")

with st.form("expense_form", clear_on_submit=True):
    expense_date = st.date_input("Date", value=date.today())
    category = st.selectbox("Category", ["Food", "Travel", "Shopping", "Bills", "Other"])
    amount = st.number_input("Amount", min_value=1, step=1)
    description = st.text_input("Description (optional)")
    submitted = st.form_submit_button("Add Expense")

    if submitted:
        new_expense = pd.DataFrame(
            [[expense_date, category, amount, description]],
            columns=["Date", "Category", "Amount", "Description"]
        )
        st.session_state.expenses = pd.concat([st.session_state.expenses, new_expense], ignore_index=True)
        st.success("✅ Expense added!")

# ===================== Expense Table =====================
st.subheader("📊 Expense History")

if not st.session_state.expenses.empty:
    st.write("Click 🗑️ to delete an expense:")

    col0, col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 3, 1])
    col0.markdown("**S.No**")
    col1.markdown("**Date**")
    col2.markdown("**Category**")
    col3.markdown("**Amount**")
    col4.markdown("**Description**")
    col5.markdown("**Delete**")

    for i, row in st.session_state.expenses.iterrows():
        col0, col1, col2, col3, col4, col5 = st.columns([1, 2, 2, 2, 3, 1])
        col0.write(i + 1)
        col1.write(row["Date"])
        col2.write(row["Category"])
        col3.write(row["Amount"])
        col4.write(row["Description"])
        if col5.button("🗑️", key=f"del{i}"):
            st.session_state.expenses.drop(i, inplace=True)
            st.session_state.expenses.reset_index(drop=True, inplace=True)
            st.rerun()

    # ===================== Chatbot =====================
    st.markdown("---")  # divider
    st.subheader("💬 Chat with Your Finance Assistant")

    # Clear Chat button
    if st.button("🗑️ Clear Chat"):
        st.session_state.messages = []
        st.session_state.last_category = None
        st.rerun()

    # Custom CSS for chat bubbles + scrollable container
    st.markdown("""
        <style>
        .chat-container {
            height: 400px;               /* fixed height */
            overflow-y: auto;            /* vertical scroll */
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 10px;
            background-color: #ffffff10; /* transparent for dark mode */
        }
        .chat-bubble-user {
            background-color: #0078FF;   /* blue */
            color: white;
            padding: 8px 12px;
            border-radius: 15px;
            margin: 5px;
            text-align: right;
            float: right;
            clear: both;
            max-width: 80%;
        }
        .chat-bubble-bot {
            background-color: #F1F0F0;   /* light gray */
            color: black;
            padding: 8px 12px;
            border-radius: 15px;
            margin: 5px;
            text-align: left;
            float: left;
            clear: both;
            max-width: 80%;
        }
        </style>
    """, unsafe_allow_html=True)

    # Chat history inside scrollable div
    chat_html = "<div class='chat-container'>"
    for message in st.session_state.messages:
        if message["role"] == "user":
            chat_html += f"<div class='chat-bubble-user'>{message['content']}</div>"
        else:
            chat_html += f"<div class='chat-bubble-bot'>{message['content']}</div>"
    chat_html += "<div id='chat-end'></div></div>"

    # Auto-scroll JS
    chat_html += """
    <script>
    var chatContainer = document.querySelector('.chat-container');
    chatContainer.scrollTop = chatContainer.scrollHeight;
    </script>
    """

    st.markdown(chat_html, unsafe_allow_html=True)

    # ===================== Chat Input =====================
    if user_input := st.chat_input("Ask me about your expenses..."):
        # Show user query immediately
        st.session_state.messages.append({"role": "user", "content": user_input})

        query = user_input.lower()
        df = st.session_state.expenses.copy()
        df["Date"] = pd.to_datetime(df["Date"])
        today = date.today()

        # --- Default response ---
        response = "🤔 Sorry, I didn’t understand that. Can you rephrase?"

        # --- Category Synonyms ---
        category_synonyms = {
            "food": ["food", "meal", "meals", "dining", "lunch", "dinner", "snacks"],
            "travel": ["travel", "trip", "taxi", "bus", "train", "flight", "cab"],
            "shopping": ["shopping", "clothes", "fashion", "purchase", "buy"],
            "bills": ["bills", "electricity", "rent", "recharge", "subscription", "utilities"],
            "other": ["other", "misc", "miscellaneous", "random"]
        }

        # --- Time Filters ---
        if "today" in query:
            df = df[df["Date"].dt.date == today]
        elif "yesterday" in query:
            df = df[df["Date"].dt.date == (today - timedelta(days=1))]
        elif "this month" in query:
            df = df[df["Date"].dt.month == today.month]

        category_sum = df.groupby("Category")["Amount"].sum() if not df.empty else pd.Series()

        # --- Casual Replies ---
        if any(word in query for word in ["hi", "hello", "hey", "yo", "hola"]):
            response = "👋 Hey there! I’m your finance buddy. Ask me about your expenses anytime!"
        elif "thanks" in query or "thank you" in query:
            response = "🙌 You’re welcome! Always here to help."
        elif "bye" in query or "goodbye" in query or "see you" in query:
            response = "👋 Bye! Take care of your expenses!"
        elif "good morning" in query:
            response = "🌞 Good morning! Ready to check your spending?"
        elif "good evening" in query:
            response = "🌆 Good evening! Let’s see how your expenses are doing."
        else:
            matched = False
            # --- Category-specific queries with synonyms ---
            for cat, synonyms in category_synonyms.items():
                if any(word in query for word in synonyms):
                    amt = df[df["Category"].str.lower() == cat]["Amount"].sum()
                    if amt > 0:
                        response = f"🛒 You’ve spent **{amt}** on {cat.capitalize()}."
                    else:
                        response = f"📭 No spending recorded for {cat.capitalize()} in this period."
                    st.session_state.last_category = cat
                    matched = True
                    break

            # --- Follow-up Queries ---
            if not matched and ("only" in query or "that category" in query or "on it" in query):
                if st.session_state.last_category:
                    amt = df[df["Category"].str.lower() == st.session_state.last_category]["Amount"].sum()
                    response = f"🔄 Continuing from before... You’ve spent **{amt}** on {st.session_state.last_category.capitalize()}."
                    matched = True

            # --- Totals / Aggregates ---
            if not matched:
                if "total" in query:
                    total = df["Amount"].sum()
                    response = f"💰 Your total spending is **{total}**."
                elif "biggest" in query or "highest" in query:
                    if not category_sum.empty:
                        biggest_cat = category_sum.idxmax()
                        biggest_amt = category_sum.max()
                        response = f"📌 Your biggest expense category is **{biggest_cat}** with {biggest_amt} spent."
                elif "smallest" in query or "least" in query:
                    if not category_sum.empty:
                        smallest_cat = category_sum.idxmin()
                        smallest_amt = category_sum.min()
                        response = f"🔻 Your smallest expense category is **{smallest_cat}** with {smallest_amt} spent."
                elif "average" in query or "avg" in query:
                    if not df.empty:
                        avg = df["Amount"].mean()
                        response = f"📊 Your average expense is **{avg:.2f}**."

        # Save bot response
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.rerun()

else:
    st.info("No expenses added yet. Add some above to get started.")
