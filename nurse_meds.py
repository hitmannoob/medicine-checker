import streamlit as st

from neo4j import GraphDatabase
from openai import OpenAI


st.set_page_config(page_title="Medicine Checker", page_icon=":hospital:", layout="wide")
col1, col2, col3 = st.columns([2, 1, 2])
col2.title(":green[Medicine Checker]")
st.markdown("***This tool helps you check if the prescribed medicine is correct or not based on the symptoms you provide.***")
URI = st.secrets["URI"]
AUTH = st.secrets["AUTH"]
driver = GraphDatabase.driver(URI, auth=AUTH)
OPENAI_KEY = st.secrets["OPENAI_KEY"]


def get_company_list():
    records , summary , keys = driver.execute_query(
        """
    MATCH (manufacturer:`Manufactuer name`)
    RETURN manufacturer.manufacturer_name AS ManufacturerName
    ORDER BY ManufacturerName
    """
    )
    company_list = []
    for record in records:
        company_list.append(record.values()[0])

    return company_list

def get_meds_list(company_name):
    records , summary , keys = driver.execute_query(
        """
    MATCH (manufacturer:`Manufactuer name` {manufacturer_name: $manufacturerName})-[:Manufacturer_Name]->(medicine:`Name of the Medicine`)
    RETURN medicine.name AS MedicineName
    ORDER BY MedicineName
        """, manufacturerName= company_name)
    meds_list = []
    for record in records:
        meds_list.append(record.values()[0])
    return meds_list

def get_info_graph(medicine_name, company_name):
    records , summary , keys = driver.execute_query(
        """
        MATCH (manufacturer:`Manufactuer name` {manufacturer_name: $manufacturerName})
MATCH (medicine:`Name of the Medicine` {name: $medicineName})
MATCH (manufacturer)-[:Manufacturer_Name]->(medicine)
OPTIONAL MATCH (medicine)-[:description]->(desc:`Description of the medicines`)
OPTIONAL MATCH (medicine)-[:Composition_of_the_medicines]->(composition:`composition of the medicine`)
OPTIONAL MATCH (composition)-[:side_effects_caused_by_the_composition]->(sideEffects:`Side effects`)
OPTIONAL MATCH (comp1:`Short Composition 1`)-[:Primary_Composition_of_the_medicine]->(composition)
OPTIONAL MATCH (comp2:`Short Composition 2`)-[:Secondary_Composition_of_the_Medicine]->(composition)

RETURN 
  medicine.name as medicine_name,
  manufacturer.manufacturer_name as manufacturer,
  desc.medicine_desc as description,
  composition.salt_composition as composition,
  sideEffects.side_effects as side_effects,
  comp1.short_composition1 as primary_composition,
  comp2.short_composition2 as secondary_composition
""", manufacturerName= company_name, medicineName= medicine_name )
    
    graph_dict = dict(zip(records[0].keys(), records[0].values()))

    return graph_dict

col1, col2 = st.columns([2, 2])
manufactuer = col1.selectbox("Select Manufactutuer", get_company_list())
drug = col2.selectbox("Select Medicine" , get_meds_list(manufactuer))
symptoms = col1.text_input("Enter Symptoms")
drug_dictionary= get_info_graph(drug, manufactuer)

client = OpenAI(
    api_key=OPENAI_KEY,
)
button1 ,button2 = st.columns([2, 2])
button = button2.button(":blue[Check Medicine]")
if button:
    with st.spinner("Checking the medicine..."):
        completion = client.chat.completions.create(
            model="gpt-4.1",

            messages=[
                {
                    "role": "developer",
                    "content": f"You are a medical assistant. You will be given a list of symptoms and a dictionary of the drug is being prescribed with its description, composition, manufactuer . You need to check if the medicine given is correct or not. Give the reasoning behind your answer. here is the dictionary of the drug: {drug_dictionary}"
                },
                {
                    "role": "user",
                    "content": f"Given the symptoms: {symptoms} , is the medicine prescribed correct?"
                }
            ]
        )
        st.success("Medicine Checked!")

        st.markdown(completion.choices[0].message.content)