# ============================================================
# BURKINA FOOD PRICE MONITOR
# ETAPE 44 : EXPLORATION INTERACTIVE DES PRIX
# ============================================================

import streamlit as st
import pandas as pd
import sqlite3
from pathlib import Path

# ------------------------------------------------------------
# 1. CONFIGURATION DE LA PAGE
# ------------------------------------------------------------

st.set_page_config(
    page_title="Burkina Food Price Monitor",
    page_icon="📊",
    layout="wide"
)

# ------------------------------------------------------------
# 2. CHEMIN DE LA BASE DE DONNEES
# ------------------------------------------------------------

# On identifie automatiquement le dossier qui contient app.py.
# Cette méthode fonctionne sur Windows comme sur Linux.

DOSSIER_PROJET = Path(__file__).resolve().parent

# On construit le chemin vers la base SQLite.
# La base doit se trouver dans data/database/.

FICHIER_BASE = (
    DOSSIER_PROJET
    / "data"
    / "database"
    / "burkina_food_price_monitor.db"
)
# ------------------------------------------------------------
# 3. CHARGEMENT DES DONNEES SQLITE
# ------------------------------------------------------------

@st.cache_data
def charger_table(nom_table):

    # Vérifier que le fichier de la base de données existe.
    if not FICHIER_BASE.is_file():
        raise FileNotFoundError(
            f"Base de données introuvable : {FICHIER_BASE}"
        )

    # Ouvrir la base SQLite en lecture seule.
    connexion = sqlite3.connect(
        FICHIER_BASE.as_uri() + "?mode=ro",
        uri=True
    )

    try:
        # Charger la table demandée dans un DataFrame Pandas.
        donnees = pd.read_sql_query(
            f"SELECT * FROM {nom_table}",
            connexion
        )

        # Retourner les données chargées.
        return donnees

    finally:
        # Fermer la connexion même si une erreur survient.
        connexion.close()
# ------------------------------------------------------------
# CHARGEMENT DES TABLES DE LA BASE DE DONNEES
# ------------------------------------------------------------

# Chargement des données des marchés.
prix_marches = charger_table("prix_marches")

# Chargement des données nationales.
prix_national = charger_table("prix_national")

# Chargement des indicateurs généraux.
indicateurs = charger_table("indicateurs_generaux")

# Conversion des dates en format datetime.
prix_marches["price_date"] = pd.to_datetime(
    prix_marches["price_date"]
)

prix_national["price_date"] = pd.to_datetime(
    prix_national["price_date"]
)
# ------------------------------------------------------------
# 4. DICTIONNAIRE DES PRODUITS
# ------------------------------------------------------------

produits = {
    "Haricot": "c_beans",
    "Maïs": "c_maize",
    "Mil": "c_millet",
    "Riz": "c_rice",
    "Sorgho": "c_sorghum"
}

# ------------------------------------------------------------
# 5. TITRE
# ------------------------------------------------------------

st.title("BURKINA FOOD PRICE MONITOR")

st.subheader(
    "Observatoire économique des prix alimentaires au Burkina Faso"
)

st.write(
    "Explorez les estimations de prix selon le produit, "
    "la région et la période."
)

st.divider()

# ------------------------------------------------------------
# 6. BARRE LATERALE : FILTRES
# ------------------------------------------------------------

st.sidebar.header("Filtres d'analyse")

# Sélection du produit
produit_selectionne = st.sidebar.selectbox(
    "Choisir un produit",
    list(produits.keys())
)

# Sélection de la colonne correspondant au produit
colonne_prix = produits[produit_selectionne]

# Liste des régions
regions = sorted(
    prix_marches["adm1_name"].dropna().unique()
)

# Ajout de l'option toutes les régions
options_regions = ["Toutes les régions"] + regions

region_selectionnee = st.sidebar.selectbox(
    "Choisir une région",
    options_regions
)

# ------------------------------------------------------------
# 7. FILTRE TEMPOREL
# ------------------------------------------------------------

date_min = prix_marches["price_date"].min().date()

date_max = prix_marches["price_date"].max().date()

periode = st.sidebar.date_input(
    "Choisir la période",
    value=(date_min, date_max),
    min_value=date_min,
    max_value=date_max,
    format="DD/MM/YYYY"
)

# Vérifier que deux dates ont été sélectionnées
if len(periode) == 2:

    date_debut = pd.Timestamp(periode[0])

    date_fin = pd.Timestamp(periode[1])

else:

    date_debut = pd.Timestamp(date_min)

    date_fin = pd.Timestamp(date_max)

# ------------------------------------------------------------
# 8. APPLICATION DES FILTRES
# ------------------------------------------------------------

donnees = prix_marches.copy()

# Filtrer le produit
donnees = donnees.dropna(
    subset=[colonne_prix]
)

# Filtrer la région si nécessaire
if region_selectionnee != "Toutes les régions":

    donnees = donnees[
        donnees["adm1_name"] == region_selectionnee
    ]

# Filtrer les dates
donnees = donnees[
    (donnees["price_date"] >= date_debut)
    &
    (donnees["price_date"] <= date_fin)
]

# ------------------------------------------------------------
# 9. CALCUL DE LA SERIE TEMPORELLE
# ------------------------------------------------------------

serie = donnees.groupby(
    "price_date"
).agg(
    prix_moyen=(colonne_prix, "mean"),
    nombre_marches=(colonne_prix, "count")
).reset_index()

serie = serie.sort_values("price_date")

# ------------------------------------------------------------
# 10. AFFICHAGE DES INDICATEURS
# ------------------------------------------------------------

st.header("Indicateurs de la sélection")

if not serie.empty:

    derniere_ligne = serie.iloc[-1]

    prix_actuel = derniere_ligne["prix_moyen"]

    date_actuelle = derniere_ligne["price_date"]

    nombre_observations = len(serie)

    nombre_marches = donnees["mkt_name"].nunique()

    # Calcul de la variation entre les deux dernières dates
    if len(serie) >= 2:

        prix_precedent = serie.iloc[-2]["prix_moyen"]

        variation = (
            (prix_actuel - prix_precedent)
            / prix_precedent
        ) * 100

    else:

        variation = None

    # Affichage des KPI
    col1, col2, col3, col4 = st.columns(4)

    col1.metric(
        "Prix moyen estimé",
        f"{prix_actuel:.2f} XOF"
    )

    col2.metric(
        "Variation précédente",
        "Non disponible" if variation is None
        else f"{variation:+.2f}%"
    )

    col3.metric(
        "Marchés concernés",
        nombre_marches
    )

    col4.metric(
        "Dernière observation",
        date_actuelle.strftime("%m/%Y")
    )

else:

    st.warning(
        "Aucune observation disponible pour cette sélection."
    )

# ------------------------------------------------------------
# 11. GRAPHIQUE INTERACTIF
# ------------------------------------------------------------

st.divider()

st.header(
    f"Évolution du prix estimé : {produit_selectionne}"
)

if not serie.empty:

    # Préparation du graphique
    graphique = serie.set_index("price_date")[
        ["prix_moyen"]
    ]

    # Affichage du graphique interactif
    st.line_chart(
        graphique,
        x_label="Date",
        y_label="Prix moyen estimé (XOF, unité de la source)",
        width="stretch"
    )

    st.caption(
        "Chaque point représente la moyenne des estimations "
        "disponibles dans les marchés de la sélection."
    )

# ------------------------------------------------------------
# 12. TABLEAU DES OBSERVATIONS
# ------------------------------------------------------------

st.divider()

st.header("Données détaillées")

if not serie.empty:

    tableau = serie.copy()

    tableau["price_date"] = (
        tableau["price_date"].dt.strftime("%Y-%m")
    )

    tableau = tableau.rename(
        columns={
            "price_date": "Date",
            "prix_moyen": "Prix moyen estimé",
            "nombre_marches": "Nombre d'observations"
        }
    )

    st.dataframe(
        tableau,
        width="stretch",
        hide_index=True
    )

    # --------------------------------------------------------
    # 13. TELECHARGEMENT DES DONNEES
    # --------------------------------------------------------

    fichier_csv = tableau.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Télécharger les données CSV",
        data=fichier_csv,
        file_name="analyse_prix_burkina.csv",
        mime="text/csv"
    )

# ------------------------------------------------------------
# 14. NOTE METHODOLOGIQUE
# ------------------------------------------------------------

st.divider()

st.caption(
    """
    Source : World Bank Microdata – Monthly food price estimates
    by product and market, Burkina Faso.

    Les données correspondent à des estimations mensuelles.
    Les moyennes régionales sont calculées à partir des marchés
    disponibles pour chaque période. Le nombre de marchés peut
    varier dans le temps.
    """
)

# ============================================================
# ETAPE 45 : COMPARAISON ECONOMIQUE DES REGIONS
# ============================================================

st.divider()

st.header("Comparaison économique des régions")

st.write(
    "Cette section compare les estimations de prix des "
    "différentes régions du Burkina Faso."
)

# ------------------------------------------------------------
# 1. PREPARATION DES DONNEES
# ------------------------------------------------------------

# On repart de la table complète des marchés.
# On ne conserve pas le filtre régional précédent :
# nous voulons comparer toutes les régions simultanément.

donnees_regionales = prix_marches.copy()

# On conserve uniquement les observations dont le prix
# du produit sélectionné est disponible.
donnees_regionales = donnees_regionales.dropna(
    subset=[colonne_prix, "adm1_name"]
)

# Application de la période choisie dans la barre latérale.
donnees_regionales = donnees_regionales[
    (donnees_regionales["price_date"] >= date_debut)
    &
    (donnees_regionales["price_date"] <= date_fin)
]

# ------------------------------------------------------------
# 2. CALCUL DES PRIX MOYENS PAR REGION ET PAR MOIS
# ------------------------------------------------------------

# Première étape :
# calculer le prix moyen dans chaque région pour chaque mois.
#
# Cette étape évite de donner davantage de poids aux mois
# qui comportent plus de marchés disponibles.

prix_mensuels_regionaux = donnees_regionales.groupby(
    ["adm1_name", "price_date"]
).agg(
    prix_mensuel=(colonne_prix, "mean"),
    nombre_marches=("mkt_name", "nunique")
).reset_index()

# ------------------------------------------------------------
# 3. CALCUL DES INDICATEURS REGIONAUX
# ------------------------------------------------------------

# Deuxième étape :
# calculer la moyenne des prix mensuels de chaque région.
#
# On calcule également le nombre moyen de marchés observés
# et le nombre de mois disponibles.

comparaison_regions = prix_mensuels_regionaux.groupby(
    "adm1_name"
).agg(
    prix_moyen=("prix_mensuel", "mean"),
    nombre_marches_moyen=("nombre_marches", "mean"),
    nombre_mois=("price_date", "nunique")
).reset_index()

# Renommer les colonnes pour obtenir un tableau lisible.
comparaison_regions = comparaison_regions.rename(
    columns={
        "adm1_name": "Région",
        "prix_moyen": "Prix moyen estimé",
        "nombre_marches_moyen": "Nombre moyen de marchés",
        "nombre_mois": "Nombre de mois"
    }
)

# Classer les régions du prix le plus élevé au plus faible.
comparaison_regions = comparaison_regions.sort_values(
    "Prix moyen estimé",
    ascending=False
).reset_index(drop=True)

# ------------------------------------------------------------
# 4. AFFICHAGE DES TROIS REGIONS LES PLUS CHERES
# ------------------------------------------------------------

st.subheader(
    f"Les régions aux prix estimés les plus élevés : {produit_selectionne}"
)

if not comparaison_regions.empty:

    trois_plus_cheres = comparaison_regions.head(3)

    col1, col2, col3 = st.columns(3)

    # Affichage des trois premières régions.
    colonnes = [col1, col2, col3]

    for i, (_, ligne) in enumerate(
        trois_plus_cheres.iterrows()
    ):

        colonnes[i].metric(
            label=f"{i + 1}. {ligne['Région']}",
            value=f"{ligne['Prix moyen estimé']:.2f} XOF"
        )

# ------------------------------------------------------------
# 5. AFFICHAGE DES TROIS REGIONS LES MOINS CHERES
# ------------------------------------------------------------

st.subheader(
    "Les régions aux prix estimés les plus faibles"
)

if not comparaison_regions.empty:

    trois_moins_cheres = comparaison_regions.tail(3)

    col1, col2, col3 = st.columns(3)

    colonnes = [col1, col2, col3]

    for i, (_, ligne) in enumerate(
        trois_moins_cheres.iterrows()
    ):

        colonnes[i].metric(
            label=f"{i + 1}. {ligne['Région']}",
            value=f"{ligne['Prix moyen estimé']:.2f} XOF"
        )

# ------------------------------------------------------------
# 6. GRAPHIQUE DE COMPARAISON REGIONALE
# ------------------------------------------------------------

st.divider()

st.subheader(
    f"Comparaison des prix régionaux : {produit_selectionne}"
)

if not comparaison_regions.empty:

    # Préparer les données du graphique.
    graphique_regions = comparaison_regions.set_index(
        "Région"
    )[["Prix moyen estimé"]]

    # Afficher le graphique en barres.
    st.bar_chart(
        graphique_regions,
        horizontal=True,
        x_label="Prix moyen estimé (XOF, unité de la source)",
        y_label="Régions",
        width="stretch"
    )

# ------------------------------------------------------------
# 7. TABLEAU DE CLASSEMENT REGIONAL
# ------------------------------------------------------------

st.divider()

st.subheader("Classement détaillé des régions")

if not comparaison_regions.empty:

    st.dataframe(
        comparaison_regions,
        width="stretch",
        hide_index=True
    )

    # --------------------------------------------------------
    # 8. TELECHARGEMENT DU CLASSEMENT
    # --------------------------------------------------------

    fichier_regions = comparaison_regions.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Télécharger le classement régional",
        data=fichier_regions,
        file_name="classement_regional_prix.csv",
        mime="text/csv"
    )

else:

    st.warning(
        "Aucune donnée régionale disponible pour cette période."
    )

# ------------------------------------------------------------
# 9. NOTE METHODOLOGIQUE
# ------------------------------------------------------------

st.caption(
    """
    Méthode : les prix sont d'abord moyennés par région et par mois.
    Les moyennes mensuelles sont ensuite agrégées sur la période
    sélectionnée. Chaque mois disponible contribue ainsi de manière
    égale à la moyenne régionale.

    Le nombre de marchés peut varier selon les régions et les mois.
    Les résultats sont descriptifs et ne permettent pas, à eux seuls,
    d'expliquer les causes des différences régionales.
    """
)
# ============================================================
# ETAPE 46 : ECARTS REGIONAUX PAR RAPPORT A LA MOYENNE NATIONALE
# ============================================================

st.divider()

st.header("Écarts régionaux par rapport à la moyenne nationale")

st.write(
    "Cette analyse mesure la différence entre les prix estimés "
    "dans chaque région et les prix moyens estimés au niveau national."
)

# ------------------------------------------------------------
# 1. PREPARATION DES DONNEES REGIONALES
# ------------------------------------------------------------

# On copie les données des marchés pour ne pas modifier
# la table originale utilisée dans les autres analyses.

donnees_ecarts = prix_marches.copy()

# On convertit les dates en format datetime.
# Cette conversion permet de comparer correctement les dates.

donnees_ecarts["price_date"] = pd.to_datetime(
    donnees_ecarts["price_date"]
)

# On conserve les observations correspondant à la période choisie.

donnees_ecarts = donnees_ecarts[
    (donnees_ecarts["price_date"] >= date_debut)
    &
    (donnees_ecarts["price_date"] <= date_fin)
]

# On retire les lignes sans prix ou sans région.

donnees_ecarts = donnees_ecarts.dropna(
    subset=[colonne_prix, "adm1_name"]
)

# ------------------------------------------------------------
# 2. CALCUL DES PRIX MOYENS REGIONAUX PAR MOIS
# ------------------------------------------------------------

# On calcule le prix moyen de chaque région pour chaque mois.
# Chaque région aura donc une valeur mensuelle.

prix_regionaux_mensuels = donnees_ecarts.groupby(
    ["adm1_name", "price_date"]
).agg(
    prix_regional=(colonne_prix, "mean")
).reset_index()

# ------------------------------------------------------------
# 3. PREPARATION DES PRIX NATIONAUX
# ------------------------------------------------------------

# On copie la table contenant les observations nationales.

donnees_nationales = prix_national.copy()

# On convertit également les dates nationales.

donnees_nationales["price_date"] = pd.to_datetime(
    donnees_nationales["price_date"]
)

# On conserve uniquement la période sélectionnée.

donnees_nationales = donnees_nationales[
    (donnees_nationales["price_date"] >= date_debut)
    &
    (donnees_nationales["price_date"] <= date_fin)
]

# On conserve uniquement les dates et les prix du produit sélectionné.

prix_nationaux_mensuels = donnees_nationales[
    ["price_date", colonne_prix]
].dropna()

# On renomme la colonne pour faciliter les calculs.

prix_nationaux_mensuels = prix_nationaux_mensuels.rename(
    columns={
        colonne_prix: "prix_national"
    }
)

# ------------------------------------------------------------
# 4. COMPARAISON DES PRIX REGIONAUX ET NATIONAUX
# ------------------------------------------------------------

# On associe à chaque prix régional le prix national
# correspondant au même mois.

ecarts_regionaux = prix_regionaux_mensuels.merge(
    prix_nationaux_mensuels,
    on="price_date",
    how="inner"
)

# On calcule l'écart en pourcentage :
#
# ((Prix régional - Prix national) / Prix national) * 100
#
# Un résultat positif signifie que le prix régional
# est supérieur à la moyenne nationale.
#
# Un résultat négatif signifie qu'il est inférieur.

ecarts_regionaux["ecart_pct"] = (
    (
        ecarts_regionaux["prix_regional"]
        -
        ecarts_regionaux["prix_national"]
    )
    /
    ecarts_regionaux["prix_national"]
) * 100

# ------------------------------------------------------------
# 5. SYNTHESE DES ECARTS PAR REGION
# ------------------------------------------------------------

# On calcule la moyenne des écarts mensuels de chaque région.

synthese_ecarts = ecarts_regionaux.groupby(
    "adm1_name"
).agg(
    ecart_moyen_pct=("ecart_pct", "mean"),
    nombre_mois=("price_date", "nunique")
).reset_index()

# On renomme les colonnes pour rendre le tableau lisible.

synthese_ecarts = synthese_ecarts.rename(
    columns={
        "adm1_name": "Région",
        "ecart_moyen_pct": "Écart moyen par rapport au national (%)",
        "nombre_mois": "Nombre de mois comparés"
    }
)

# On classe les régions de l'écart le plus élevé au plus faible.

synthese_ecarts = synthese_ecarts.sort_values(
    "Écart moyen par rapport au national (%)",
    ascending=False
).reset_index(drop=True)

# ------------------------------------------------------------
# 6. AFFICHAGE DES RESULTATS
# ------------------------------------------------------------

if not synthese_ecarts.empty:

    # On identifie la région présentant l'écart positif le plus élevé.

    region_plus_chere = synthese_ecarts.iloc[0]

    # On identifie la région présentant l'écart le plus faible.

    region_moins_chere = synthese_ecarts.iloc[-1]

    col1, col2 = st.columns(2)

    col1.metric(
        label="Écart régional moyen le plus élevé",
        value=(
            f"{region_plus_chere['Écart moyen par rapport au national (%)']:.2f}%"
        ),
        help=region_plus_chere["Région"]
    )

    col2.metric(
        label="Écart régional moyen le plus faible",
        value=(
            f"{region_moins_chere['Écart moyen par rapport au national (%)']:.2f}%"
        ),
        help=region_moins_chere["Région"]
    )

    # --------------------------------------------------------
    # 7. GRAPHIQUE DES ECARTS REGIONAUX
    # --------------------------------------------------------

    st.subheader(
        f"Écart moyen des prix régionaux par rapport au national : "
        f"{produit_selectionne}"
    )

    graphique_ecarts = synthese_ecarts.set_index(
        "Région"
    )[["Écart moyen par rapport au national (%)"]]

    st.bar_chart(
        graphique_ecarts,
        horizontal=True,
        x_label="Écart moyen (%)",
        y_label="Régions",
        width="stretch"
    )

    # --------------------------------------------------------
    # 8. TABLEAU DETAILLE
    # --------------------------------------------------------

    st.subheader("Tableau détaillé des écarts régionaux")

    st.dataframe(
        synthese_ecarts,
        width="stretch",
        hide_index=True
    )

    # --------------------------------------------------------
    # 9. TELECHARGEMENT DES RESULTATS
    # --------------------------------------------------------

    fichier_ecarts = synthese_ecarts.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Télécharger les écarts régionaux",
        data=fichier_ecarts,
        file_name="ecarts_regionaux_national.csv",
        mime="text/csv"
    )

else:

    st.warning(
        "Aucune donnée disponible pour effectuer cette comparaison."
    )

# ------------------------------------------------------------
# 10. NOTE METHODOLOGIQUE
# ------------------------------------------------------------

st.caption(
    """
    Méthode : pour chaque mois, le prix moyen estimé de chaque région
    est comparé au prix estimé de la moyenne nationale.

    L'écart est calculé en pourcentage par rapport au prix national.
    Les écarts mensuels sont ensuite moyennés sur la période sélectionnée.

    Un écart positif indique un prix régional supérieur à la référence
    nationale ; un écart négatif indique un prix inférieur.

    Ces résultats sont descriptifs et ne permettent pas d'identifier
    les causes économiques des différences observées.
    """
)
# ============================================================
# ETAPE 47 : DETECTION DES VARIATIONS ANORMALES DES PRIX
# ============================================================

st.divider()

st.header("Détection des variations anormales des prix")

st.write(
    "Ce module identifie les hausses et les baisses mensuelles "
    "inhabituelles des prix alimentaires dans les régions "
    "du Burkina Faso."
)

# ------------------------------------------------------------
# 1. PREPARATION DES DONNEES
# ------------------------------------------------------------

# On copie la base des observations des marchés.
# Cela évite de modifier la table originale.

donnees_anomalies = prix_marches.copy()

# On convertit la date en format datetime.
# Ce format permet de classer correctement les mois.

donnees_anomalies["price_date"] = pd.to_datetime(
    donnees_anomalies["price_date"]
)

# On conserve les observations correspondant à la période choisie.

donnees_anomalies = donnees_anomalies[
    (donnees_anomalies["price_date"] >= date_debut)
    &
    (donnees_anomalies["price_date"] <= date_fin)
]

# On retire les observations sans prix ou sans région.

donnees_anomalies = donnees_anomalies.dropna(
    subset=[colonne_prix, "adm1_name"]
)

# ------------------------------------------------------------
# 2. CALCUL DES PRIX MOYENS MENSUELS PAR REGION
# ------------------------------------------------------------

# Pour chaque région et chaque mois, on calcule le prix moyen.
# Cela permet de suivre l'évolution mensuelle des prix régionaux.

prix_mensuels_anomalies = donnees_anomalies.groupby(
    ["adm1_name", "price_date"]
).agg(
    prix_moyen=(colonne_prix, "mean")
).reset_index()

# On classe les observations par région et par date.

prix_mensuels_anomalies = prix_mensuels_anomalies.sort_values(
    ["adm1_name", "price_date"]
)

# ------------------------------------------------------------
# 3. CALCUL DES VARIATIONS MENSUELLES
# ------------------------------------------------------------

# On calcule le prix du mois précédent pour chaque région.

prix_mensuels_anomalies["prix_precedent"] = (
    prix_mensuels_anomalies.groupby("adm1_name")["prix_moyen"]
    .shift(1)
)

# On calcule également le nombre de mois écoulés entre
# deux observations successives.

prix_mensuels_anomalies["mois_actuel"] = (
    prix_mensuels_anomalies["price_date"].dt.year * 12
    +
    prix_mensuels_anomalies["price_date"].dt.month
)

prix_mensuels_anomalies["mois_precedent"] = (
    prix_mensuels_anomalies.groupby("adm1_name")["mois_actuel"]
    .shift(1)
)

# On calcule la variation en pourcentage uniquement lorsque
# les deux observations correspondent à des mois consécutifs.

prix_mensuels_anomalies["variation_pct"] = (
    (
        prix_mensuels_anomalies["prix_moyen"]
        -
        prix_mensuels_anomalies["prix_precedent"]
    )
    /
    prix_mensuels_anomalies["prix_precedent"]
) * 100

# On écarte les variations calculées sur des mois non consécutifs.

prix_mensuels_anomalies.loc[
    prix_mensuels_anomalies["mois_actuel"]
    - prix_mensuels_anomalies["mois_precedent"] != 1,
    "variation_pct"
] = float("nan")

# On retire les observations sans variation calculable.

prix_mensuels_anomalies = prix_mensuels_anomalies.dropna(
    subset=["variation_pct"]
)

# ------------------------------------------------------------
# 4. CALCUL DES SEUILS STATISTIQUES
# ------------------------------------------------------------

# Pour chaque région, on calcule :
# - la variation mensuelle moyenne ;
# - l'écart-type des variations mensuelles.

prix_mensuels_anomalies["variation_moyenne"] = (
    prix_mensuels_anomalies.groupby("adm1_name")["variation_pct"]
    .transform("mean")
)

prix_mensuels_anomalies["ecart_type"] = (
    prix_mensuels_anomalies.groupby("adm1_name")["variation_pct"]
    .transform("std")
)

# On définit les limites inférieure et supérieure.
#
# Limite supérieure = moyenne + 2 écarts-types.
# Limite inférieure = moyenne - 2 écarts-types.

prix_mensuels_anomalies["seuil_superieur"] = (
    prix_mensuels_anomalies["variation_moyenne"]
    +
    2 * prix_mensuels_anomalies["ecart_type"]
)

prix_mensuels_anomalies["seuil_inferieur"] = (
    prix_mensuels_anomalies["variation_moyenne"]
    -
    2 * prix_mensuels_anomalies["ecart_type"]
)

# ------------------------------------------------------------
# 5. IDENTIFICATION DES VARIATIONS ANORMALES
# ------------------------------------------------------------

# Une hausse anormale dépasse le seuil supérieur.
# Une baisse anormale est inférieure au seuil inférieur.

conditions = [
    prix_mensuels_anomalies["variation_pct"]
    > prix_mensuels_anomalies["seuil_superieur"],

    prix_mensuels_anomalies["variation_pct"]
    < prix_mensuels_anomalies["seuil_inferieur"]
]

# On attribue une catégorie à chaque observation.

prix_mensuels_anomalies["type_anomalie"] = pd.Series(
    "Variation normale",
    index=prix_mensuels_anomalies.index
)

prix_mensuels_anomalies.loc[
    conditions[0],
    "type_anomalie"
] = "Hausse anormale"

prix_mensuels_anomalies.loc[
    conditions[1],
    "type_anomalie"
] = "Baisse anormale"

# On conserve uniquement les variations anormales.

anomalies_detectees = prix_mensuels_anomalies[
    prix_mensuels_anomalies["type_anomalie"] != "Variation normale"
].copy()

# ------------------------------------------------------------
# 6. AFFICHAGE DES INDICATEURS
# ------------------------------------------------------------

st.subheader("Synthèse de la détection")

nombre_anomalies = len(anomalies_detectees)

nombre_hausses = (
    anomalies_detectees["type_anomalie"]
    == "Hausse anormale"
).sum()

nombre_baisses = (
    anomalies_detectees["type_anomalie"]
    == "Baisse anormale"
).sum()

col1, col2, col3 = st.columns(3)

col1.metric(
    "Variations anormales détectées",
    nombre_anomalies
)

col2.metric(
    "Hausses anormales",
    int(nombre_hausses)
)

col3.metric(
    "Baisses anormales",
    int(nombre_baisses)
)

# ------------------------------------------------------------
# 7. TABLEAU DES ANOMALIES
# ------------------------------------------------------------

st.subheader("Observations détectées")

if not anomalies_detectees.empty:

    # On prépare un tableau contenant uniquement
    # les informations utiles à l'analyse.

    tableau_anomalies = anomalies_detectees[
        [
            "price_date",
            "adm1_name",
            "prix_precedent",
            "prix_moyen",
            "variation_pct",
            "type_anomalie"
        ]
    ].copy()

    # On renomme les colonnes.

    tableau_anomalies = tableau_anomalies.rename(
        columns={
            "price_date": "Date",
            "adm1_name": "Région",
            "prix_precedent": "Prix du mois précédent",
            "prix_moyen": "Prix du mois actuel",
            "variation_pct": "Variation mensuelle (%)",
            "type_anomalie": "Type d'anomalie"
        }
    )

    # On affiche les anomalies les plus importantes en premier.

    tableau_anomalies = tableau_anomalies.sort_values(
        "Variation mensuelle (%)",
        ascending=False
    )

    st.dataframe(
        tableau_anomalies,
        width="stretch",
        hide_index=True
    )

    # --------------------------------------------------------
    # 8. GRAPHIQUE DES ANOMALIES
    # --------------------------------------------------------

    st.subheader("Répartition des variations anormales")

    graphique_anomalies = (
        anomalies_detectees.groupby(
            ["adm1_name", "type_anomalie"]
        )
        .size()
        .unstack(fill_value=0)
    )

    st.bar_chart(
        graphique_anomalies,
        width="stretch"
    )

    # --------------------------------------------------------
    # 9. TELECHARGEMENT DES RESULTATS
    # --------------------------------------------------------

    fichier_anomalies = tableau_anomalies.to_csv(
        index=False
    ).encode("utf-8-sig")

    st.download_button(
        label="Télécharger les anomalies détectées",
        data=fichier_anomalies,
        file_name="anomalies_prix_regionaux.csv",
        mime="text/csv"
    )

else:

    st.success(
        "Aucune variation anormale détectée pour ce produit "
        "sur la période sélectionnée."
    )

# ------------------------------------------------------------
# 10. NOTE METHODOLOGIQUE
# ------------------------------------------------------------

st.caption(
    """
    Méthode : les prix moyens sont calculés par région et par mois.
    Les variations mensuelles sont ensuite comparées à leur moyenne
    régionale, à l'aide d'un seuil de deux écarts-types.

    Une hausse ou une baisse dépassant ces limites est signalée
    comme statistiquement inhabituelle.

    Les variations ne sont calculées que lorsque deux mois
    consécutifs sont disponibles.

    Une anomalie statistique ne constitue pas nécessairement
    une crise alimentaire. Elle doit faire l'objet d'une analyse
    complémentaire avant toute interprétation économique.
    """
)
