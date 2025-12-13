# Configuration Systemd pour la mise à jour automatique

Ce dossier contient les fichiers systemd pour planifier l'exécution automatique du script `update_database.sh` tous les lundis à 20h.

## Fichiers

- `bases-athle-update.service` : Service systemd qui exécute le script de mise à jour
- `bases-athle-update.timer` : Timer systemd qui déclenche le service tous les lundis à 20h

## Installation

### 1. Copier les fichiers dans le répertoire systemd

```bash
sudo cp systemd/bases-athle-update.service /etc/systemd/system/
sudo cp systemd/bases-athle-update.timer /etc/systemd/system/
```

### 2. Recharger la configuration systemd

```bash
sudo systemctl daemon-reload
```

### 3. Activer et démarrer le timer

```bash
# Activer le timer pour qu'il démarre automatiquement au boot
sudo systemctl enable bases-athle-update.timer

# Démarrer le timer immédiatement
sudo systemctl start bases-athle-update.timer
```

## Vérification

### Vérifier le status du timer

```bash
systemctl status bases-athle-update.timer
```

### Voir les prochaines exécutions planifiées

```bash
systemctl list-timers bases-athle-update.timer
```

### Voir les logs du service

```bash
journalctl -u bases-athle-update.service
```

### Voir les logs en temps réel

```bash
journalctl -u bases-athle-update.service -f
```

## Test manuel

### Exécuter le service manuellement (sans attendre le timer)

```bash
sudo systemctl start bases-athle-update.service
```

### Vérifier le résultat

```bash
systemctl status bases-athle-update.service
# ou
cat /home/cyril/src/mypacer/mypacer_scraper/update.log
```

## Gestion

### Arrêter le timer

```bash
sudo systemctl stop bases-athle-update.timer
```

### Désactiver le timer (ne démarre plus au boot)

```bash
sudo systemctl disable bases-athle-update.timer
```

### Redémarrer le timer après modification

```bash
sudo systemctl daemon-reload
sudo systemctl restart bases-athle-update.timer
```

## Notes

- Le timer ajoute un délai aléatoire de 0 à 15 minutes pour éviter les pics de charge
- Si le système est éteint au moment de l'exécution, la tâche sera rattrapée au prochain démarrage grâce à `Persistent=true`
- Les logs sont écrits dans `/home/cyril/src/mypacer/mypacer_scraper/update.log`
- Les logs systemd sont accessibles via `journalctl`
