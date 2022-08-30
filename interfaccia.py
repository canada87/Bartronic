import streamlit as st
import gspread
import pandas as pd
import time

tab1, tab2 = st.tabs(["Cocktails", "Calibration"])
cread_file = "bartronic-38ca80d51b42.json"

gc = gspread.service_account(cread_file)
db = gc.open("tabella_live")
wks_live = db.get_worksheet(0)
data1 = wks_live.get_all_records()
df_live = pd.DataFrame(data1).iloc[[0], :].astype(float)
df_calib = pd.DataFrame(data1).iloc[[1], 2:].astype(float)
df_pompe = pd.DataFrame(data1).iloc[[2], 2:].T

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

    if st.button("Is the robot available?"):
        wks_live.update_cell(2, 2, 0)
        time.sleep(2)
        gc = gspread.service_account(cread_file)
        db = gc.open("tabella_live")
        wks_live = db.get_worksheet(0)
        data1 = wks_live.get_all_records()
        df_live = pd.DataFrame(data1)
        if df_live.loc[df_live.index[0], 'onoff'] == 0:
            st.error('Not Available')
        else:
            st.success('Available')

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

    # si cicla su tutti i componenti del cocktail selezionato
    for liquid in componetns.columns:
        # si seleziona la pompa che ha quel liquido richiesto
        if liquid in pump_state:
            # si estrae il numero della pompa
            num_pompa = pump_state.index(liquid) + 1
            # si estrae la quantita di quel liquido dal db
            quantity = df_cocktails.loc[df_cocktails['name'] == choice, liquid].values[0]
            # conversione da ml a secondi
            quantity = round(quantity/speed, 1)*df_calib.loc[df_calib.index[0], 'p'+str(num_pompa)]
            # si va a scrivere quella quantita sulla pompa selezionata nel df che deve essere caricato a db
            df_live.loc[df_live.index[0], 'p'+str(num_pompa)] = quantity

    st.table(df_live)

    max_time = df_live.loc[df_live.index[0], :].max()

    if st.button("Serve"):
        cell_list = wks_live.range('C2:J2')
        for i, cell in enumerate(cell_list):
            cell.value = df_live.loc[df_live.index[0], 'p'+str(i+1)]
            wks_live.update_cells(cell_list)

        wks_live.update_cell(2, 1, 1)

        with st.spinner('Serving'):
            time.sleep(max_time)
        # todo mettere un controllo che fa tornare disponibile la scelta dei cocktail quando il db fa tornare
        #  disponibile il valore go della tabella
        st.success('Done!')

with tab2:
    st.header("Calibration")
    pump_selected_calib = st.selectbox("select pump: ", [i + 1 for i in range(df_calib.shape[1])])
    number = st.number_input('Insert a number', value=float(df_calib.loc[df_calib.index[0], 'p'+str(pump_selected_calib)]), step=0.1)
    st.dataframe(df_calib)
    if st.button("load"):
        wks_live.update_cell(3, pump_selected_calib+2, number)



