# Carburants

Prix des carburants en temps réel, sur carte : https://carburants.matthv.com

Page statique, sans serveur applicatif. Le navigateur interroge directement :

- les prix : flux instantané officiel sur data.economie.gouv.fr (`prix-des-carburants-en-france-flux-instantane-v2`, endpoint `exports/json`, sans clé) ;
- les adresses : Géoplateforme de l'IGN (`data.geopf.fr/geocodage`) ;
- la carte : Leaflet (cdnjs) et les tuiles OpenStreetMap.

Le point de départ est l'Hôtel de Ville de Poitiers. On peut le remplacer par une adresse, la position du téléphone
ou la zone affichée sur la carte. Le carburant, le rayon et le point de départ sont gardés en cookies.

## Fichiers

- `www/` : ce qui est servi tel quel (page, manifeste PWA, icônes).
- `www/noms.json` : noms et enseignes des stations, **généré**, hors dépôt.
- `outils/maj-noms.py` : récupère ces noms sur prix-carburants.gouv.fr, à défaut sur OpenStreetMap, pour la Vienne
  et les départements voisins (86, 79, 49, 37, 36, 87, 16). Lancé chaque lundi par cron (~5 min).
- `outils/icones.py` : génère les PNG à partir du même dessin que `www/favicon.svg` (à modifier aux deux endroits).

Le flux officiel ne donne pas les noms des stations, et prix-carburants.gouv.fr n'autorise pas les appels depuis
un navigateur : d'où le fichier préparé côté serveur.

## Mise à jour

Le site lit directement ce dossier : un commit + push suffit, il n'y a pas d'étape de déploiement.
