# BURKINA FOOD PRICE MONITOR 🇧🇫

### Observatoire économique des prix alimentaires au Burkina Faso

**BURKINA FOOD PRICE MONITOR** est un projet de Data Analytics développé entièrement en Python. Il vise à analyser et suivre l'évolution des prix alimentaires au Burkina Faso à travers le temps et les régions.

L'objectif est de transformer des données économiques réelles en indicateurs, visualisations et outils interactifs d'aide à la compréhension des dynamiques de prix.

## 🎯 Objectifs du projet

- Suivre l'évolution des prix des principaux produits alimentaires.
- Analyser les variations mensuelles et les épisodes de fortes fluctuations.
- Comparer les niveaux de prix entre les régions.
- Identifier les disparités géographiques.
- Construire un tableau de bord interactif accessible en ligne.

## 🌾 Produits étudiés

Cinq produits alimentaires sont analysés :

- Haricot
- Maïs
- Mil
- Riz
- Sorgho

## 📊 Analyses réalisées

- Évolution de l'indice national des prix alimentaires.
- Comparaison des prix estimés des produits.
- Analyse de la dispersion relative des prix.
- Calcul des variations mensuelles.
- Identification des hausses et baisses importantes.
- Analyse des variations saisonnières.
- Comparaison régionale des prix.
- Calcul des écarts de prix entre régions.
- Analyse des évolutions régionales sur longue période.
- Calcul du taux de croissance annuel moyen (TCAM).
- Détection statistique de variations inhabituelles.

## 🛠️ Technologies utilisées

- Python
- Pandas
- NumPy
- SQLite
- Streamlit
- Matplotlib
- Analyse statistique et visualisation de données

## 🗂️ Structure du projet

```text
BURKINA-FOOD-PRICE-MONITOR/
│
├── app.py
├── requirements.txt
├── README.md
│
└── data/
    └── database/
        └── burkina_food_price_monitor.db
```

## 📚 Source des données

**World Bank Microdata Library**

Dataset : Monthly food price estimates by product and market – Burkina Faso.

[Consulter la source officielle](https://datacatalog.worldbank.org/search/dataset/0060170/burkina-faso-monthly-food-price-estimates-by-product-and-market)

Les estimations de prix proviennent d'une méthodologie utilisant notamment des modèles d'apprentissage automatique pour estimer les prix sur les marchés et périodes concernés. Elles ne doivent donc pas être assimilées systématiquement à des prix directement observés lors d'enquêtes.

## ⚠️ Limites méthodologiques

- Les prix étudiés sont des estimations issues de la source.
- Les variations observées ne permettent pas, à elles seules, d'établir des relations causales.
- Les comparaisons régionales sont descriptives et ne sont pas pondérées par les volumes commercialisés ou la population.
- Les évolutions nominales des prix ne constituent pas directement une mesure de l'inflation officielle ou du pouvoir d'achat.

## 🚀 Tableau de bord

Application développée avec Streamlit.

**Lien du tableau de bord :** À venir.

## 👨‍💻 Auteur

Projet personnel de Data Analytics consacré à l'analyse économique des prix alimentaires au Burkina Faso.

**Compétences mobilisées :** collecte et préparation des données, analyse statistique, Python, SQL, visualisation et développement d'applications interactives.
