#!/bin/bash
set -e # Stop le script en cas d'erreur
FILENAME="update_gvx_3140_$(date +%F).zip"
trap 'echo "Erreur : le téléchargement ou l extraction a échoué." >&2' ERR
echo "Téléchargement du firmware..."
wget "https://www.grandstream.com/hubfs/IoT%20Team/Release_GXV3140_1.0.7.80.zip" -O "$FILENAME"
echo "Extraction des fichiers..."
unzip "$FILENAME"
echo "Script exécuté avec succès."
