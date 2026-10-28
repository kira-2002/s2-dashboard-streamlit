
from pathlib import Path

import pandas as pd
import plotly.express as px
import streamlit as st

# Configuration de la page
st.set_page_config(
    page_title="Dashboard agricole africain",
    page_icon=" ",
    layout="wide"
)

# Titre
st.title(" Dashboard de la production agricole en Afrique")
st.markdown(
    "Explore les données de production agricole des pays africains "
    "à partir des données FAOSTAT."
)


# Chargement des données pour le dashboard
@st.cache_data
def charger_donnees():
    chemin_csv = (
        Path(__file__).parent
        / "data"
        / "processed"
        / "production_dashboard.csv"
    )

    df = pd.read_csv(chemin_csv)

    df["Year"] = pd.to_numeric(df["Year"], errors="coerce")
    df["Value"] = pd.to_numeric(df["Value"], errors="coerce")

    df = df.dropna(subset=["Area", "Item", "Year", "Value"])
    df["Year"] = df["Year"].astype(int)

    return df


df = charger_donnees()

# Les données du CSV sont déjà filtrées sur Production et l'unité tonne.
production = df.copy()
production = production.dropna(subset=["Area", "Item", "Year", "Value"])

# Indicateurs principaux
st.subheader(" Indicateurs clés")

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Pays disponibles", production["Area"].nunique())

with col2:
    st.metric("Produits agricoles", production["Item"].nunique())

with col3:
    st.metric(
        "Années couvertes",
        f"{production['Year'].min()} – {production['Year'].max()}"
    )

st.divider()

# Filtres dans la barre latérale
st.sidebar.header("Filtres")

pays_disponibles = sorted(production["Area"].unique())
pays_selectionnes = st.sidebar.multiselect(
    "Sélectionner les pays",
    pays_disponibles,
    default=["Senegal"] if "Senegal" in pays_disponibles else pays_disponibles[:3]
)

annees_disponibles = sorted(production["Year"].unique())
annee_selectionnee = st.sidebar.selectbox(
    "Année",
    annees_disponibles,
    index=len(annees_disponibles) - 1
)

produits_disponibles = sorted(production["Item"].unique())
produit_selectionne = st.sidebar.selectbox(
    "Produit agricole",
    produits_disponibles,
    index=produits_disponibles.index("Maize (corn)")
    if "Maize (corn)" in produits_disponibles else 0
)

# Application des filtres
donnees_filtrees = production[
    production["Area"].isin(pays_selectionnes)
    & (production["Year"] == annee_selectionnee)
    & (production["Item"] == produit_selectionne)
]

st.subheader(
    f"Production de {produit_selectionne} en {annee_selectionnee}"
)

if donnees_filtrees.empty:
    st.warning("Aucune donnée disponible pour cette sélection.")
else:
    graphique = px.bar(
        donnees_filtrees.sort_values("Value", ascending=True),
        x="Value",
        y="Area",
        orientation="h",
        labels={
            "Value": "Production (tonnes)",
            "Area": "Pays"
        },
        title="Comparaison de la production entre les pays"
    )
    graphique.update_layout(template="plotly_white")
    st.plotly_chart(graphique, width="stretch")

# Deuxième graphique : évolution annuelle de la production
st.divider()
st.subheader(" Évolution de la production au fil des années")

pays_evolution = st.selectbox(
    "Choisir un pays pour analyser son évolution",
    sorted(production["Area"].unique()),
    index=(
        sorted(production["Area"].unique()).index("Senegal")
        if "Senegal" in production["Area"].unique()
        else 0
    ),
    key="pays_evolution"
)

produit_evolution = st.selectbox(
    "Choisir un produit pour cette évolution",
    sorted(production["Item"].unique()),
    index=(
        sorted(production["Item"].unique()).index("Maize (corn)")
        if "Maize (corn)" in production["Item"].unique()
        else 0
    ),
    key="produit_evolution"
)

evolution = production[
    (production["Area"] == pays_evolution)
    & (production["Item"] == produit_evolution)
].dropna(subset=["Value"])

if evolution.empty:
    st.warning("Aucune donnée disponible pour cette sélection.")
else:
    fig_evolution = px.line(
        evolution.sort_values("Year"),
        x="Year",
        y="Value",
        markers=True,
        title=f"Évolution de {produit_evolution} — {pays_evolution}",
        labels={
            "Year": "Année",
            "Value": "Production (tonnes)"
        }
    )

    fig_evolution.update_layout(template="plotly_white")
    st.plotly_chart(fig_evolution, width="stretch")

# Troisième graphique : principaux produits agricoles
st.divider()
st.subheader(" Principaux produits agricoles")

pays_produits = st.selectbox(
    "Choisir un pays pour comparer ses produits",
    sorted(production["Area"].unique()),
    index=(
        sorted(production["Area"].unique()).index("Senegal")
        if "Senegal" in production["Area"].unique()
        else 0
    ),
    key="pays_produits"
)

annee_produits = st.selectbox(
    "Choisir une année pour la comparaison",
    sorted(production["Year"].unique()),
    index=len(sorted(production["Year"].unique())) - 1,
    key="annee_produits"
)

donnees_produits = production[
    (production["Area"] == pays_produits)
    & (production["Year"] == annee_produits)
].dropna(subset=["Value"])

# Exclure les catégories agrégées pour limiter les doubles comptes
categories_agregees = [
    "Cereals, primary",
    "Fruit Primary",
    "Vegetables Primary",
    "Roots and Tubers, Total",
    "Sugar Crops Primary",
    "Milk, Total",
    "Meat, Total",
    "Pulses, Total",
    "Citrus Fruit, Total",
    "Treenuts, Total",
    "Eggs Primary"
]

donnees_produits = donnees_produits[
    ~donnees_produits["Item"].isin(categories_agregees)
]

top_produits = (
    donnees_produits
    .sort_values("Value", ascending=False)
    .head(10)
    .sort_values("Value", ascending=True)
)

if top_produits.empty:
    st.warning("Aucune donnée disponible pour cette sélection.")
else:
    fig_produits = px.bar(
        top_produits,
        x="Value",
        y="Item",
        orientation="h",
        title=f"Top 10 des produits — {pays_produits}, {annee_produits}",
        labels={
            "Value": "Production (tonnes)",
            "Item": "Produit agricole"
        },
        hover_data={"Value": ":,.0f"}
    )

    fig_produits.update_layout(template="plotly_white")
    st.plotly_chart(fig_produits, width="stretch")

# Quatrième graphique : comparaison entre pays
st.divider()
st.subheader(" Comparaison de la production entre pays")

produit_pays = st.selectbox(
    "Choisir un produit à comparer entre pays",
    sorted(production["Item"].unique()),
    index=(
        sorted(production["Item"].unique()).index("Maize (corn)")
        if "Maize (corn)" in production["Item"].unique()
        else 0
    ),
    key="produit_pays"
)

annee_pays = st.selectbox(
    "Choisir l'année de comparaison",
    sorted(production["Year"].unique()),
    index=len(sorted(production["Year"].unique())) - 1,
    key="annee_pays"
)

donnees_pays = production[
    (production["Item"] == produit_pays)
    & (production["Year"] == annee_pays)
].dropna(subset=["Value"])

top_pays = (
    donnees_pays
    .sort_values("Value", ascending=False)
    .head(10)
    .sort_values("Value", ascending=True)
)

if top_pays.empty:
    st.warning("Aucune donnée disponible pour cette sélection.")
else:
    fig_pays = px.bar(
        top_pays,
        x="Value",
        y="Area",
        orientation="h",
        title=f"Top 10 des pays — {produit_pays}, {annee_pays}",
        labels={
            "Value": "Production (tonnes)",
            "Area": "Pays"
        },
        hover_data={"Value": ":,.0f"}
    )

    fig_pays.update_layout(template="plotly_white")
    st.plotly_chart(fig_pays, width="stretch")

# Cinquième graphique : distribution des productions
st.divider()
st.subheader("Distribution des volumes de production")

produit_distribution = st.selectbox(
    "Choisir un produit pour analyser sa distribution",
    sorted(production["Item"].unique()),
    index=(
        sorted(production["Item"].unique()).index("Maize (corn)")
        if "Maize (corn)" in production["Item"].unique()
        else 0
    ),
    key="produit_distribution"
)

annee_distribution = st.selectbox(
    "Choisir l'année pour la distribution",
    sorted(production["Year"].unique()),
    index=len(sorted(production["Year"].unique())) - 1,
    key="annee_distribution"
)

donnees_distribution = production[
    (production["Item"] == produit_distribution)
    & (production["Year"] == annee_distribution)
].dropna(subset=["Value"])

if donnees_distribution.empty:
    st.warning("Aucune donnée disponible pour cette sélection.")
else:
    fig_distribution = px.histogram(
        donnees_distribution,
        x="Value",
        nbins=20,
        title=(
            f"Répartition des productions de {produit_distribution} "
            f"en {annee_distribution}"
        ),
        labels={
            "Value": "Production (tonnes)",
            "count": "Nombre de pays"
        }
    )

    fig_distribution.update_layout(template="plotly_white")
    st.plotly_chart(fig_distribution, width="stretch")

    st.caption(
        "Chaque barre représente une tranche de volumes de production. "
        "Les valeurs extrêmes peuvent rendre la distribution asymétrique."
    )

# Aperçu du tableau
with st.expander("Afficher les données utilisées"):
    st.dataframe(donnees_filtrees, width="stretch")
