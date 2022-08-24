import streamlit as st

choice = st.selectbox("select your cocktail", ("Gin Tonic", "London Mule", "Corpse Revival"))

ingredients = ["empty", "sciroppo di zucchero", "Gin", "Tonica", "Vino Bianco", "Contrau", "sciroppo di zenzero",
               "succo di arancia", "succo di limone", "succo di lime"]

st.sidebar.write("Pumps content")
pump1 = st.sidebar.selectbox("select the content of the pump 1", ingredients)
pump2 = st.sidebar.selectbox("select the content of the pump 2", ingredients)
pump3 = st.sidebar.selectbox("select the content of the pump 3", ingredients)
pump4 = st.sidebar.selectbox("select the content of the pump 4", ingredients)
pump5 = st.sidebar.selectbox("select the content of the pump 5", ingredients)
pump6 = st.sidebar.selectbox("select the content of the pump 6", ingredients)
pump7 = st.sidebar.selectbox("select the content of the pump 7", ingredients)
pump8 = st.sidebar.selectbox("select the content of the pump 8", ingredients)

if choice == "Gin Tonic":
    st.write("Gin Tonic ingredients:")
elif choice == "London Mule":
    st.write("London Mule ingredients:")
elif choice == "Corpse Revival":
    st.write("Corpse Revival ingredients:")

if st.button("serve"):
    st.write("serving")

