import sqlite3 as sql
import numpy as np

## Variables globales
dico_pts = {0:0, 1:0, 2:0, 3:8, 4:16, 5:32, 6:48, 7:64, 8:96, 9:128, 10:256}

## Fonctions

#===============================================================================
def interrogation(requete) :
    """
    Entrée : requete (chaîne de caractères) : requête SQL d'une interrogation de la base de données
    Sortie : liste de tuples
    """
    # Connexion à la base de données :
    bdd = sql.connect(u'IMC.sqlite')
    curseur = bdd.cursor()

    # Interrogation de la base de données :
    curseur.execute(requete)
    resultat = curseur.fetchall()

    # Fermeture de la base de données :
    bdd.close()

    # Renvoi des résultats :
    return resultat


#===============================================================================
def calcul_score_partie(nom_joueur, partie):
    """
    entrée : - nom_joueur (str) : nom d'un joueur
             - partie (tuple) : Informations sur la partie. Les éléments du tuple sont les valeurs des attributs dans la table
             Parties de la base de données :
                 -> partie[0] : identifiant de la partie (entier)
                 -> partie[1] : date (str)
                 -> partie[2] : nom du joueur 1 (str)
                 -> partie[3] : nom du joueur 2 (str)
                 -> partie[4] : nom du joueur 3 (str)
                 -> partie[5] : nom du joueur 4 (str)
                 -> partie[6] : nom du joueur situé à l'est dans la partie (str)
                 -> partie[7] : nom du gagnant (str)
                 -> partie[8] : type de victoire (str)
                 -> partie[9] : nom du joueur ayant éventuellement défaussé la tuile ayant permis le mahjong (str)
                 -> partie[10] : nombre de fan bonus (int)
                 -> partie[11] : nombre de tuiles restant dans le mur à la fin de la partie (int)
                 -> partie[12] : identifiant de la main révélée par le joueur gagnant (int)
    sortie : (entier) évolution du score du joueur après la partie
    """
    if partie[8] == "nul" :
        #--- Partie nulle, sans gagnant (lau4 guk6) ---
        return 0
    elif nom_joueur != partie[2] and nom_joueur != partie[3] and nom_joueur != partie[4] and nom_joueur != partie[5] :
        #--- Le joueur n'a pas participé à la partie ---
        return 0
    else :
        #--- Récupération du nb de fan de base ---
        requete = """ SELECT nb_fan FROM Mains WHERE id_main = {0}""".format(partie[12])
        resultat = interrogation(requete)
        if len(resultat) != 1 :
            raise ValueError("Erreur : La main d'indice {0} n'a pas été trouvée dans la table Mains. Résultat renvoyé :{1}".format(partie[12], resultat))
        nb_fan = resultat[0][0]
        #--- Ajout des fans bonus pour avoir le nombre de fan total ---
        nb_fan_tot = nb_fan + partie[10]
        #--- Conversion du nombre de fan en points de base ---
        if nb_fan_tot > 10 :
            nb_fan_tot = 10
        pts_base = dico_pts[nb_fan_tot]

        #-----------------------------------------------------
        #--------- Cas où le joueur a perdu la partie --------
        #-----------------------------------------------------
        if nom_joueur != partie[7] :
            facteur = -1
            if nom_joueur == partie[6] :
                #--- Doublement des points perdus si le joueur est l'est ---
                facteur *= 2
            elif partie[7] == partie[6] :
                #--- Doublement des points perdus si le joueur gagnant est l'est ---
                facteur *= 2

            if partie[8] == 'muraille' :
                #--- Doublement des points perdus si la tuile gagnante a été piochée dans le mur ---
                facteur *= 2
            elif nom_joueur == partie[9] :
                #--- Doublement des points perdus si le joueur a défaussé la tuile gagnante ---
                facteur *= 2

            return facteur * pts_base
        #-----------------------------------------------------
        #--------- Cas où le joueur a gagné la partie --------
        #-----------------------------------------------------
        else :
            if partie[8] == 'muraille' :
                #--- Partie gagnée en piochant une tuile de la muraille ---
                if partie[7] == partie[6] :
                    #--- Le gagnant est l'est ---
                    facteur = 12
                else :
                    facteur = 8
            else :
                #--- Partie gagnée en piochant une tuile défaussée ---
                if partie[7] == partie[6] :
                    #--- Le gagnant est l'est ---
                    facteur = 8
                else :
                    if partie[6] == partie[9] :
                        #--- Le joueur à l'est a défaussé la tuile gagnante ---
                        facteur = 6
                    else :
                        facteur = 5

            return facteur * pts_base


#===============================================================================
def creer_liste_joueurs(tous=False):
    """
    Retourne la liste de tous les joueurs ayant fait une partie dans la base de données.
    """
    requete = """ SELECT DISTINCT j1 FROM Parties
                  UNION
                  SELECT DISTINCT j2 FROM Parties
                  UNION
                  SELECT DISTINCT j3 FROM Parties
                  UNION
                  SELECT DISTINCT j4 FROM Parties
              """
    resultats = interrogation(requete)

    if tous :
        return [resultats[i][0] for i in range(len(resultats))]
    else :
        return [resultats[i][0] for i in range(len(resultats)) if resultats[i][0] != 'Apolline']


#===============================================================================
def calcul_nb_parties(nom_joueur):
    """
    Retourne le nombre de parties qui ont été faite par un certain joueur.
    """
    requete = """ SELECT COUNT(*) FROM Parties
                  WHERE j1 = '{0}' OR j2 = '{0}' OR j3 = '{0}' OR j4 = '{0}'
              """.format(nom_joueur)
    resultats = interrogation(requete)
    return resultats[0][0]


#===============================================================================
def calcul_score_joueur_total(nom_joueur):
    """
    entrée : nom_joueur (str) : nom d'un joueur
    sortie : L_scores (liste d'entiers) Liste des scores du joueur. Contient autant d'éléments qu'il y a de parties enregistrées.
             Si le joueur n'a pas participé à une partie, un score identique au score précédent est ajouté à la liste.
    """
    #--- Récupération de la liste de toutes les parties ---
    requete = """ SELECT * FROM Parties ORDER BY id_partie"""
    L_parties = interrogation(requete)

    #--- Création de la liste des scores en fonction du numéro des parties ---
    L_scores = []
    score_tot = 0

    for partie in L_parties :
        score = calcul_score_partie(nom_joueur, partie)
        score_tot += score
        L_scores.append(score_tot)

    return L_scores


#===============================================================================
def calcul_score_joueur_total_2(nom_joueur):
    """
    entrée : nom_joueur (str) : nom d'un joueur
    sortie : L_scores (liste d'entiers) Liste des scores du joueur. Contient autant d'éléments qu'il y a de parties jouées par le joueur.
    """

    #--- Création de la liste des scores en fonction du nombre de parties ---
    requete = """ SELECT * FROM Parties
                  WHERE j1 = '{0}' OR j2 = '{0}' OR j3 = '{0}' OR j4 = '{0}'
              """.format(nom_joueur)
    L_parties = interrogation(requete)

    L_scores = []
    score_tot = 0

    for partie in L_parties :
        score = calcul_score_partie(nom_joueur, partie)
        score_tot += score
        L_scores.append(score_tot)

    return L_scores


#===============================================================================
def get_classement(seuil_nb_parties):
    """
    entrée : seuil_nb_parties (int) : Seuls les scores des personnes ayant fait plus de parties que cette valeur seuil seront représentés
    sortie : liste de tuples (nom, score, nb_parties) avec :
        - nom (str) : le nom du joueur
        - score (int) : le score du joueur après la dernière partie
        - nb_parties (int) : nombre de parties faites par chaque joueur
    """
    L_joueurs = creer_liste_joueurs()
    L_classement = []

    for joueur in L_joueurs :
        nb_parties = calcul_nb_parties(joueur)
        if nb_parties > seuil_nb_parties :
            dernier_score = calcul_score_joueur_total(joueur)[-1]
            L_classement.append([joueur, dernier_score, nb_parties])

    L_classement.sort(key=lambda c:-c[1])

    return L_classement


#===============================================================================
def get_classement_groupe(L_joueurs) :
    """
    entrée : L_joueurs (list) : Liste de 4 chaînes de caractères correspondant aux
    joueurs d'un groupe donné
    sortie : Nombre de parties jouées par le groupe (int), L_scores
        L_scores est une liste de listes. Chaque sous-liste contient deux éléments, le premier est le nom du joueur (str), le deuxième est la liste des scores de toutes les parties du joueur.
    """
    #--- Récupération de la liste de toutes les parties du groupe ---
    requete = """SELECT * FROM Parties
                   WHERE j1 IN ("{0}", "{1}", "{2}", "{3}")
                   AND j2 IN ("{0}", "{1}", "{2}", "{3}")
                   AND j3 IN ("{0}", "{1}", "{2}", "{3}")
                   AND j4 IN ("{0}", "{1}", "{2}", "{3}")
                   ORDER BY id_partie""".format(*L_joueurs)
    L_parties = interrogation(requete)

    #--- Création de la liste des scores des 4 joueurs ---
    L_scores = [[L_joueurs[i],[]] for i in range(len(L_joueurs))]
    if len(L_parties) > 0 :
        for i in range(len(L_joueurs)) :
            nom_joueur = L_joueurs[i]
            score_tot = 0
            for partie in L_parties :
                score = calcul_score_partie(nom_joueur, partie)
                score_tot += score
                L_scores[i][1].append(score_tot)
        L_scores.sort(key=lambda c:-c[1][-1])
    return len(L_parties), L_scores


#===============================================================================
def get_parties_victoires(seuil_nb_parties):
    """
    Sortie : dictionnaire dont les clés sont les noms des joueurs (str) et les valeurs
        sont les listes [nb de parties, nb de victoires, % de victoire, % est, % tuile gagnante défaussée, % victoire est]
    """
    L_noms_joueurs = creer_liste_joueurs()
    D = {}
    for joueur in L_noms_joueurs :
        nb_parties = calcul_nb_parties(joueur)
        if nb_parties > seuil_nb_parties :
            D[joueur] = [nb_parties]

    for joueur in D :
        #--- Récupération du nombre et du pourcentage de victoires ---
        requete = """SELECT COUNT(*) FROM Parties WHERE gagnant = '{0}'""".format(joueur)
        nb_victoires = interrogation(requete)[0][0]
        D[joueur].append(nb_victoires)
        D[joueur].append(100*nb_victoires/D[joueur][0])

        #--- Récupération du pourcentage de fois où chaque joueur a été l'Est ---
        requete = """SELECT COUNT(*) FROM Parties WHERE joueur_est = '{0}'""".format(joueur)
        nb_est = interrogation(requete)[0][0]
        D[joueur].append(100*nb_est/D[joueur][0])

        #--- Récupération du pourcentage de fois où chaque joueur a défaussé la tuile gagnante ---
        # Nb de tuiles défaussé / Nb de parties auquel le joueur ayant participé et s'étant
        # finie sur une tuile défaussée (les parties nulles ou finies depuis la muraille
        # ne sont pas prises en compte)
        requete = """SELECT COUNT(*) FROM Parties WHERE joueur_defausse = '{0}'""".format(joueur)
        nb_defausse = interrogation(requete)[0][0]
        requete = """ SELECT COUNT(*) FROM Parties
                    WHERE (j1 = '{0}' OR j2 = '{0}' OR j3 = '{0}' OR j4 = '{0}')
                    AND type_victoire='defausse'
                """.format(joueur)
        nb_sikwu_joueur = interrogation(requete)[0][0]
        D[joueur].append(100*nb_defausse/nb_sikwu_joueur)

        #--- Récupération du pourcentage de fois où chaque joueur a gagné en étant l'Est ---
        requete = """SELECT COUNT(*) FROM Parties WHERE joueur_est = '{0}' AND gagnant='{0}'""".format(joueur)
        nb_victoire_est = interrogation(requete)[0][0]
        D[joueur].append(100*nb_victoire_est/nb_est)

    return D


#===============================================================================
def get_scenario_fin():
    """
    sortie :
        - L_type_victoire : liste de tuples (type de victoire, fréquence)
        - L_type_mains : liste de tuples (type de mains, fréquence)
        - L_nb_fan : liste de tuples (nombre de fans total, fréquence)
    """
    #--- Récupération des types de victoire ---
    Dico_type_victoire = {'defausse':'Tuile défaussée', 'muraille':'Tuile de la muraille', 'nul' :'Partie nulle'}
    requete = """SELECT type_victoire, COUNT(*) FROM Parties GROUP BY type_victoire"""
    resultats = interrogation(requete)
    L_type_victoire = [(Dico_type_victoire[resultats[i][0]], resultats[i][1]) for i in range(len(resultats))]
    #--- Récupération des types de mains ---
    requete = """SELECT Mains.nom_main, COUNT(*) FROM Parties JOIN Mains
                     ON Mains.id_main = Parties.id_main
                     WHERE Mains.nom_main != 'Main inconnue'
                     GROUP BY Mains.nom_main"""
    L_type_mains = interrogation(requete)
    #--- Récupération du nombre de fans total ---
    requete = """SELECT (Parties.nb_fan_bonus + Mains.nb_fan) AS nb_fan_tot, COUNT(*)
                     FROM Parties JOIN Mains
                     ON Mains.id_main = Parties.id_main
                         WHERE Parties.type_victoire != 'nul'
                         GROUP BY nb_fan_tot"""
    L_nb_fan = interrogation(requete)
    return L_type_victoire, L_type_mains, L_nb_fan


#===============================================================================
def get_mains_joueurs(seuil_nb_parties):
    """
    entrée : seuil_nb_parties (int) : Seuls les valeurs des personnes ayant fait plus de parties que cette valeur seuil seront renvoyées
    sortie : - L_gagnants (list of str) : liste des noms des joueurs ayant fait strictement plus de parties que le seuil
             - L_mains (list of str) : liste des noms des mains déjà réalisées dans une partie
             - L_mains_joueurs (tableau numpy) : tableau à deux dimensions contenant le nombre de mains de chaque type réalisées par chaque joueur
             - L_fans_tot (list of float) : liste du nombre de fan total de toutes les parties
             - L_points_joueurs (liste de liste d'entiers) : chaque sous-liste correspond à la liste des points remportés dans chaque partie d'un joueur
    """
    #--- Récupération de la liste des gagnants dont la main n'est pas inconnue (id 22) ---
    requete = """SELECT gagnant, COUNT(*) FROM Parties
                         WHERE id_main != 22
                         GROUP BY gagnant
              """
    resultats = interrogation(requete)
    # Tri par ordre décroissant du nombre de victoires
    resultats.sort(key=lambda c:-c[1])
    # Limitation aux joueurs ayant joué strictement plus de seuil_nb_parties parties
    L_gagnants = []
    for res in resultats :
        nom_joueur = res[0]
        if calcul_nb_parties(nom_joueur) > seuil_nb_parties :
            L_gagnants.append(nom_joueur)
    D_gagnants = {L_gagnants[i]:i for i in range(len(L_gagnants))}

    #--- Récupération de la liste des mains ---
    requete = """SELECT DISTINCT Mains.nom_main
                     FROM Parties JOIN Mains
                     ON Mains.id_main = Parties.id_main
                         WHERE Mains.nom_main != 'Main inconnue'
              """
    L_mains = [resultat[0] for resultat in interrogation(requete)]
    D_mains = {L_mains[i]:i for i in range(len(L_mains))}

    #--- Récupération du nombre de mains de chaque type par gagnant ---
    requete = """SELECT gagnant, Mains.nom_main, COUNT(*)
                     FROM Parties JOIN Mains
                     ON Mains.id_main = Parties.id_main
                         WHERE Mains.nom_main != 'Main inconnue'
                         GROUP BY gagnant, Mains.nom_main"""
    resultats = interrogation(requete)

    L_mains_joueurs = np.zeros((len(L_mains),len(L_gagnants)))
    for t in resultats :
        if t[0] in D_gagnants :  # On vérifie que le joueur t[0] a joué suffisamment de parties
            L_mains_joueurs[D_mains[t[1]], D_gagnants[t[0]]] = t[2]

    #--- Récupération du nombre de fans total par gagnant ---
    L_fans_tot = []

    for gagnant in L_gagnants :
        requete = """SELECT (Parties.nb_fan_bonus + Mains.nb_fan) AS nb_fan_tot
                     FROM Parties JOIN Mains
                     ON Mains.id_main = Parties.id_main
                         WHERE Parties.gagnant = '{0}'
                  """.format(gagnant)
        L_fans_tot.append([1.0*res[0] for res in interrogation(requete)])


    #--- Récupération du nombre moyen de points par gagnant ---
    L_points_joueurs = []

    for gagnant in L_gagnants :
        L_points = 1*[]
        # Récupération de la liste des parties gagnées par le joueur :
        requete = """SELECT * FROM Parties WHERE Parties.gagnant = '{0}'""".format(gagnant)
        L_parties = interrogation(requete)
        # Calcul des points gagnés à chaque partie :
        for partie in L_parties :
            L_points.append(calcul_score_partie(gagnant, partie))
        # Calcul de la valeur moyenne et de son incertitude :
        L_points_joueurs.append(L_points)

    return L_gagnants, L_mains, L_mains_joueurs, L_fans_tot, L_points_joueurs


#===============================================================================
def get_nb_tuiles_restantes(seuil_nb_parties):
    """
    entrée : seuil_nb_parties (int) : Seuls les valeurs des personnes ayant fait plus de parties que cette valeur seuil seront renvoyées
    sortie : - L_nb_tuile_parties (list of float) : Liste du nombre de tuiles restants dans le mur pour toutes les parties dont cette donnée est connue
             - L_gagnants (list of str) : liste des noms des joueurs ayant fait strictement plus de parties que le seuil
             - L_tuiles_joueurs (liste de liste de float) : pour chaque joueur, liste de toutes les tuiles restantes lors de ses victoires
             - L_mains (list of str) : liste de toutes les mains connues pour lesquelles le nombre de tuiles restantes est également connue.
             - L_tuiles_mains (liste de liste de float) : pour chaque main, liste de toutes les tuiles restantes lors de la victoire
    Remarque : pour une raison mystérieuse le nombre de tuiles restantes est codée sous forme de chaînes de caractères dans la base de données ... La conversion en entier est nécessaire
    """
    #--- Récupération du nombre de tuiles restants dans le mur pour toutes les parties dont cette donnée est connue ---
    requete = """SELECT nb_tuiles_restantes FROM Parties WHERE nb_tuiles_restantes IS NOT NULL"""
    L_nb_tuile_parties = [1.0*int(res[0]) for res in interrogation(requete)]

    #--- Récupération du nombre de tuiles restants par gagnant ---
    requete = """SELECT gagnant, COUNT(*) FROM Parties
                         WHERE id_main != 22 and nb_tuiles_restantes IS NOT NULL
                         GROUP BY gagnant
              """
    resultats = interrogation(requete)
    # Tri par ordre décroissant du nombre de victoires
    resultats.sort(key=lambda c:-c[1])
    # Limitation de la liste des joueurs à ceux ayant joué strictement plus de seuil_nb_parties parties
    L_gagnants = []
    for res in resultats :
        nom_joueur = res[0]
        if calcul_nb_parties(nom_joueur) > seuil_nb_parties :
            L_gagnants.append(nom_joueur)
    # Calcul du nombre de tuiles restants par joueur :
    L_tuiles_joueurs = []
    for gagnant in L_gagnants :
        # Récupération de la liste des tuiles restantes lorsque le joueur a gagné :
        requete = """SELECT nb_tuiles_restantes FROM Parties
                         WHERE nb_tuiles_restantes IS NOT NULL AND Parties.gagnant = '{0}'""".format(gagnant)
        L_tuiles_joueurs.append([1.0*int(res[0]) for res in interrogation(requete)])

    #--- Récupération du nombre de tuiles restants par main ---
    requete = """SELECT Mains.nom_main, COUNT(*)
                     FROM Parties JOIN Mains
                     ON Mains.id_main = Parties.id_main
                         WHERE Mains.nom_main != 'Main inconnue' AND nb_tuiles_restantes IS NOT NULL
						 GROUP BY Mains.nom_main
              """
    resultats = interrogation(requete)
    # Tri par ordre décroissant du nombre de mains
    resultats.sort(key=lambda c:-c[1])
    L_mains = [res[0] for res in resultats]
    # Calcul du nombre de tuiles restants par mains :
    L_tuiles_mains = []
    for main in L_mains :
        requete = """SELECT nb_tuiles_restantes FROM Parties JOIN Mains
                         ON Mains.id_main = Parties.id_main
                         WHERE nb_tuiles_restantes IS NOT NULL AND Mains.nom_main = '{0}'""".format(main)
        L_tuiles_mains.append([1.0*int(res[0]) for res in interrogation(requete)])

    return L_nb_tuile_parties, L_gagnants, L_tuiles_joueurs, L_mains, L_tuiles_mains


#===============================================================================
def get_groupes(seuil_nb_parties):
    """
    entrée : seuil_nb_parties (int) : Seuls les valeurs des personnes ayant fait plus de parties que cette valeur seuil seront renvoyées
    sortie : - L_groupes : liste de tuples dont le premier élément est un tuple contenant le nom des 4 joueurs d'un groupe et le second élément est le nombre de parties fait par ce groupe
             - len_max (int) : longueur maximale de la chaîne de caractères correspondant au nom des joueurs
    """
    #--- Appel de la fonction creer_liste_joueurs pour supprimer du résultat certains joueurs ---
    L_joueurs = creer_liste_joueurs()
    len_max = 0  # Longueur maximale du nom d'un joueur
    for joueur in L_joueurs :
        if len(joueur) > len_max :
            len_max = len(joueur)
    #--- Récupération de la liste de tous les groupes de 4 joueurs ---
    requete = """SELECT j1, j2, j3, j4 FROM Parties"""
    L_parties = interrogation(requete)
    #--- Création d'un dictionnaire de tous les groupes associé à leur nombre de parties ---
    D_groupes = {}
    for partie in L_parties :
        # Vérification que les joueurs du groupe soient tous dans la liste L_joueurs :
        if partie[0] in L_joueurs and partie[1] in L_joueurs and partie[2] in L_joueurs and partie[3] in L_joueurs :
            # Tri des joueurs par ordre alphabétique :
            groupe = list(partie)
            groupe.sort()
            groupe = tuple(groupe)
            # Ajout du groupe dans le dictionnaire :
            if groupe in D_groupes :
                D_groupes[groupe] += 1
            else :
                D_groupes[groupe] = 1
    #--- Création de la liste renvoyée, en supprimant les groupes ayant fait moins de seuil_nb_parties parties ---
    L_groupes = []
    for groupe in D_groupes :
        if D_groupes[groupe] > seuil_nb_parties :
            L_groupes.append((groupe,D_groupes[groupe]))
    L_groupes.sort(key=lambda c:-c[1])
    return L_groupes, len_max