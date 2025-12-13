# Docker Cron avec Supercronic

Ce document explique comment fonctionne l'automatisation du scraper avec Supercronic dans Docker.

## 🕐 Planification Actuelle

**Tâche** : Mise à jour de la base de données
**Script** : `./update_database.sh`
**Fréquence** : Tous les lundis à 3h00 du matin
**Crontab** : `0 3 * * 1`

## 🚀 Démarrage

### Démarrer le conteneur avec cron automatique

```bash
docker-compose up -d
```

Le conteneur démarre Supercronic qui :
- ✅ Reste actif en arrière-plan
- ✅ Exécute `update_database.sh` tous les lundis à 3h
- ✅ Log les exécutions dans `/app/logs/cron.log`

### Vérifier que Supercronic fonctionne

```bash
# Voir les logs du conteneur
docker-compose logs -f scraper

# Vérifier que Supercronic est lancé
docker-compose exec scraper ps aux | grep supercronic
```

---

## 🔧 Exécution Manuelle

### Option 1 : Exécuter dans le conteneur en cours

```bash
# Entrer dans le conteneur
docker-compose exec scraper bash

# Lancer le script manuellement
./update_database.sh

# Ou la mise à jour complète
./populate_database.sh
```

### Option 2 : Exécuter depuis l'extérieur

```bash
# Lancer update_database.sh
docker-compose exec scraper ./update_database.sh

# Lancer populate_database.sh
docker-compose exec scraper ./populate_database.sh
```

### Option 3 : Run one-shot (sans Supercronic)

```bash
# Lancer un conteneur temporaire pour populate_database.sh
docker-compose run --rm scraper ./populate_database.sh
```

---

## 📋 Modifier la Planification

### Exemples de crontab

Éditez le fichier `crontab` à la racine du projet :

```bash
# Tous les jours à 2h du matin
0 2 * * * cd /app && ./update_database.sh >> /app/logs/cron.log 2>&1

# Tous les lundis et jeudis à 3h
0 3 * * 1,4 cd /app && ./update_database.sh >> /app/logs/cron.log 2>&1

# Tous les premiers du mois à 1h
0 1 1 * * cd /app && ./update_database.sh >> /app/logs/cron.log 2>&1

# Toutes les 6 heures
0 */6 * * * cd /app && ./update_database.sh >> /app/logs/cron.log 2>&1
```

### Appliquer les modifications

```bash
# Reconstruire l'image avec le nouveau crontab
docker-compose build scraper

# Redémarrer le conteneur
docker-compose restart scraper
```

---

## 📊 Monitoring

### Voir les logs de cron

```bash
# Logs en temps réel
docker-compose exec scraper tail -f /app/logs/cron.log

# Dernières lignes
docker-compose exec scraper tail -100 /app/logs/cron.log

# Voir tous les logs
docker-compose exec scraper cat /app/logs/cron.log
```

### Vérifier la prochaine exécution

Supercronic affiche dans les logs du conteneur quand la prochaine tâche sera exécutée :

```bash
docker-compose logs scraper | grep "next"
```

### Tester la configuration crontab

```bash
# Vérifier la syntaxe (depuis le conteneur)
docker-compose exec scraper supercronic -test /app/crontab
```

---

## 🐛 Dépannage

### Le cron ne s'exécute pas

1. **Vérifier que Supercronic tourne** :
   ```bash
   docker-compose exec scraper ps aux
   ```
   Vous devriez voir : `supercronic /app/crontab`

2. **Vérifier les logs Supercronic** :
   ```bash
   docker-compose logs scraper
   ```

3. **Tester manuellement le script** :
   ```bash
   docker-compose exec scraper ./update_database.sh
   ```

### Le conteneur redémarre en boucle

```bash
# Voir les logs d'erreur
docker-compose logs scraper

# Vérifier que le fichier crontab existe
docker-compose exec scraper cat /app/crontab
```

### Permissions sur les scripts

```bash
# Vérifier les permissions
docker-compose exec scraper ls -la *.sh

# Rendre exécutable si nécessaire (rebuild requis)
chmod +x populate_database.sh update_database.sh
docker-compose build scraper
docker-compose up -d scraper
```

---

## 🔍 Différences avec systemd

| Caractéristique | Systemd | Supercronic |
|-----------------|---------|-------------|
| **Installation** | Lourd (nécessite init) | Léger (binaire statique) |
| **Logs** | journalctl | Stdout/fichier |
| **Configuration** | .service + .timer | Simple crontab |
| **Docker-friendly** | ❌ Non recommandé | ✅ Conçu pour Docker |
| **Debugging** | Complexe | Simple (logs directs) |

---

## 📚 Ressources

- [Supercronic GitHub](https://github.com/aptible/supercronic)
- [Crontab syntax](https://crontab.guru/)
- [Docker best practices](https://docs.docker.com/develop/dev-best-practices/)

---

## ⚠️ Notes Importantes

1. **Timezone** : Par défaut, le conteneur utilise UTC. Si vous voulez un fuseau horaire différent :
   ```dockerfile
   ENV TZ=Europe/Paris
   RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone
   ```

2. **Variables d'environnement** : Les variables `.env` sont disponibles car docker-compose les injecte.

3. **Overlap protection** : Supercronic empêche les exécutions simultanées du même job.

4. **Logs rotation** : Pensez à mettre en place une rotation des logs pour éviter qu'ils grossissent trop :
   ```bash
   # Ajouter dans crontab :
   0 0 * * 0 find /app/logs -name "*.log" -mtime +30 -delete
   ```
