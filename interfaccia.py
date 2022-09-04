import streamlit as st
import gspread
import pandas as pd
import time
# https://docs.streamlit.io/knowledge-base/deploy/authentication-without-sso
tab1, tab2, tab3 = st.tabs(["Cocktails", "Calibration", "Cleaning"])
cread_file = "bartronic-38ca80d51b42.json"

gc = gspread.service_account(cread_file)
db = gc.open("tabella_live")
wks_live = db.get_worksheet(0)
data1 = wks_live.get_all_records()
df_live = pd.DataFrame(data1).iloc[[0], 10]
df_calib = pd.DataFrame(data1).iloc[[1], 2:10].astype(float)
df_pompe = pd.DataFrame(data1).iloc[[2], 2:10].T

db = gc.open("tabella_cocktails")
wks_cocktail = db.get_worksheet(0)
data1 = wks_cocktail.get_all_records()
df_cocktails = pd.DataFrame(data1)
df_cocktails = df_cocktails.replace(0, pd.NA)

with tab1:
    cocktail = df_cocktails['name'].tolist()
    orginal_ingredients = df_cocktails.columns.tolist()
    orginal_ingredients.remove('name')
    orginal_ingredients.append('empty')
    pump_list = orginal_ingredients.copy()

    st.sidebar.write("Pumps content")
    table_pompe = st.sidebar.empty()
    table_pompe.write(df_pompe)
    pump_selected = st.sidebar.selectbox("pump number: ", [i+1 for i in range(df_pompe.shape[0])])

    # lista delle componenti nelle pompe a database
    pump_state = df_pompe.loc[:, df_pompe.columns[0]].tolist()
    # lista delle componenti tra cui si puo scegliere, in pratica quelle che non sono in una pompa
    pump_list = list(set(pump_list).difference(pump_state))
    # l'empty deve essere sempre disponibile quindi viene reinserito se non c'e'
    pump_list = pump_list + ["empty"] if not ("empty" in pump_list) else pump_list
    # il liquido che e' gia nella pompa deve essere presente nella lista quindi viene reinserito
    if df_pompe.loc['p'+str(pump_selected), df_pompe.columns[0]] != "empty":
        pump_list = pump_list + [df_pompe.loc['p'+str(pump_selected), df_pompe.columns[0]]]
    # si seleziona il liquido da sostituire dalla lista di quelli disponibili
    selection = st.sidebar.selectbox("pump "+str(pump_selected), pump_list,
                                     pump_list.index(df_pompe.loc['p'+str(pump_selected), df_pompe.columns[0]]))
    # sostituisco la selezione al vettore degli elementi nelle pompe
    pump_state[pump_selected-1] = selection
    # se il nuovo elemento e' diverso da quello nel db allora vado ad aggiornare il db
    if pump_state[pump_selected-1] != df_pompe.loc['p'+str(pump_selected), df_pompe.columns[0]]:
        wks_live.update_cell(4, pump_selected+2, pump_state[pump_selected-1])
        df_pompe.loc['p'+str(pump_selected), df_pompe.columns[0]] = pump_state[pump_selected-1]
        table_pompe.write(df_pompe)

    available_cocktails = []
    # vengono selezionati solo i cocktail che si possono fare con i liquidi nelle pompe
    for cock in cocktail:
        cocktail_componets = df_cocktails.loc[df_cocktails['name'] == cock, df_cocktails.columns.difference(['name'])].dropna(axis=1).columns.tolist()
        unique_liquid = list(set(cocktail_componets) & set(pump_state))
        if len(unique_liquid) == len(cocktail_componets):
            available_cocktails.append(cock)

    if len(available_cocktails) == 0:
        st.stop()

    choice = st.selectbox("select your cocktail", available_cocktails)
    componetns = df_cocktails.loc[df_cocktails['name'] == choice, df_cocktails.columns.difference(['name'])].dropna(axis=1)

    st.write('----')
    st.write(f"ingredienti del {choice}:")
    st.write(componetns.iloc[0])

    speed = 200.1/60  # ml/sec

    st.write(df_live)
    st.write(df_pompe)

    quantity = []
    num_pompa = []

    # si cicla su tutti i componenti del cocktail selezionato
    for jj, liquid in enumerate(componetns.columns):
        # si seleziona la pompa che ha quel liquido richiesto
        if liquid in pump_state:
            # si estrae il numero della pompa
            num_pompa.append(pump_state.index(liquid) + 1)
            # si estrae la quantita di quel liquido dal db
            quantity.append(df_cocktails.loc[df_cocktails['name'] == choice, liquid].values[0])
            # conversione da ml a secondi
            quantity[jj] = round(quantity[jj]/speed, 1)*df_calib.loc[df_calib.index[0], 'p'+str(num_pompa[jj])]
            # si va a scrivere quella quantita sulla pompa selezionata nel df che deve essere caricato a db
            # df_live.loc[df_live.index[0], 'p'+str(num_pompa)] = quantity

    df_to_serve = pd.DataFrame([0 for i in range(8)], [i+1 for i in range(8)], columns=['quantity'])

    for ii, num in enumerate(num_pompa):
        df_to_serve.iloc[num-1, 0] = quantity[ii]

    df_to_serve = df_to_serve.sort_values(by=['quantity'])

    # df_to_serve = pd.DataFrame(quantity, num_pompa, columns=['quantity']).sort_values(by=['quantity'])

    val_to_publish = ''
    # imposto il numero delle pompe
    for i in range(df_to_serve.shape[0]):
        val_to_publish += (str(df_to_serve.index[i]) + "-")

    # val_to_publish += 'n-'

    # imposto i tempi
    for i in range(df_to_serve.shape[0]):
        val_to_publish += (str(df_to_serve.iloc[i, 0].round(1)) + "-")

    max_time = df_to_serve.iloc[:, 0].max()

    st.write(df_to_serve)
    st.write(val_to_publish)

    if st.button("Serve"):
        val_to_publish_up = "1-"+val_to_publish
        wks_live.update_cell(2, 11, val_to_publish_up)
        with st.spinner('Serving'):
            time.sleep(max_time+5)
        val_to_publish_up = "0-"+val_to_publish
        wks_live.update_cell(2, 11, val_to_publish_up)
        st.success('Done!')

with tab2:
    st.header("Calibration")
    pump_selected_calib = st.selectbox("select pump: ", [i + 1 for i in range(df_calib.shape[1])])
    number = st.number_input('Insert a number', value=float(df_calib.loc[df_calib.index[0], 'p'+str(pump_selected_calib)]), step=0.1)
    st.dataframe(df_calib)
    if st.button("load"):
        wks_live.update_cell(3, pump_selected_calib+2, number)

with tab3:
    st.header("Cleaning")
    number = st.number_input('Cleaning time', value=3)
    cleaning_selection = st.multiselect("Pumps to clean", [i+1 for i in range(8)])

    df_to_clean = pd.DataFrame([0 for i in range(8)], [i+1 for i in range(8)], columns=['quantity'])
    for ii, num in enumerate(cleaning_selection):
        df_to_clean.iloc[num-1, 0] = number
    df_to_clean = df_to_clean.sort_values(by=['quantity'])

    val_to_clean = ''
    # imposto il numero delle pompe
    for i in range(df_to_clean.shape[0]):
        val_to_clean += (str(df_to_clean.index[i]) + "-")
    # val_to_clean += 'n-'
    # imposto i tempi
    for i in range(df_to_clean.shape[0]):
        val_to_clean += (str(df_to_clean.iloc[i, 0].round(1)) + "-")

    if st.button("Cleaning"):
        val_to_clean_up = "1-"+val_to_clean
        wks_live.update_cell(2, 11, val_to_clean_up)
        with st.spinner('Cleaning!'):
            time.sleep(number+5)
        val_to_clean_up = "0-"+val_to_clean
        wks_live.update_cell(2, 11, val_to_clean_up)
        st.success('Done!')
