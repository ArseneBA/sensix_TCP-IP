# Communication TCP/IP entre python et LabView:

Dans le cadre de notre projet, nous utilisons un des pédales sensix contenant des capteurs. Les données récoltés par les capteurs sont envoyées à une boîte d'acquisition de la marque National-Instrument pour traitement. La carte NI (National-Instrument) est programmée en LabView, les données sont donc disponible sur cette interface de programmation. Pour récupérer les données, il est donc nécessaire de faire communiquer LabView avec python. Il a été choisi d'utiliser le protocol TCP/IP pour cette communication, car celui-ci est très versatile, peut s'interfacer avec de nombreux langages et est simple d'utilisation.



## TCP/IP python - Le client:

Le code python se base sur un code préexistant développé pour le logicielle biosiglive, il a été modifié pour s'adapter au mieux à notre problématique.

Par exemple, le transtypage des données vers des "bytes" (octet) se fait avec le module struct.pack (et unpack dans le cas inverse) contraitement au module JSON dans le cas de biosiglive. Celui-ci permet en effet de préciser si les données doivent être écrite en little ou big endian (dans notre cas, on respecte le standard réseau, on utilise donc le big endian).

Autre exemple, dans le cas de biosiglive, on ouvre la connexion et on la ferme à chaque itération. Tandis que dans notre cas, pour des raisons d'optimisation, on ouvre le port une  seule fois au début.



Le client contient la table de correspondance entre le nom des données et leur coordonnées dans la matrice. Pour l'exemple, on suppose que les données sont structurées comme suit dans une matrice de 15 lignes, 10 colonnes:

- Les forces gauches et droites sont sur la première ligne, chaque force est décomposée en 3 valeurs selon les axes x, y et z (6 valeurs). La nomenclature est FGx pour force gauche sur l'axe x. Ordonnées de droite à gauche avec premièrement les forces relatives au côté gauche puis droit, et en suivant l'ordre x, y et z.

- Les moments sont sur la 3 ème ligne et se décompose de la même manière

- Les torques sont sur la 5ème ligne, il y a le torque gauche et le torque droit.

- les angles sont sur la 7ème ligne, il y a les angles gauche et droit.

- Le reste des données ne sont pour l'instant pas utilisées dans notre exemple.



## TCP/IP Labview - Le server:

### Structure des données sur Labview:

La donnée se présente sous forme d'une matrice 15 lignes 10 colonnes de floats 32 ("data array.vi"). Elle est pour l'instant générée aléatoirement après un temps choisit dans "data array refresh.vi". 

Cette création de données se faisant dans une boucle while indépendante de la boucle while du programme principal, on doit créer une queue permettant aux deux process de communiquer. Celle-ci ne contient au maximum qu'un seul élément, lors de la génération d'une nouvelle matrice, on vide la queue s'il est pleine pour venir écrire la nouvelle donnée.

## Utilisation de la version non intégrée au programme:

1. Ouvrir le fichier client.py et choisir le mode d’exécution.
2. Ouvrir le fichier  Server_LabView.vi.
3. Si l'on veut modifier la fréquence de génération de donnée, cela peut se faire en modifiant le paramètre "Generation period (ms)"
4. Lancer l'exécution de Server_LabView.vi.
5. Lancer l'exécution de client.py.

## Intégration au programme existant "I-Crankset":

Pour intégrer notre module TCP/IP au programme existant, il est nécessaire de:

- Donner la matrice (ou sont type, c'est à dire une matrice de taille équivalente) des données générées à l'entrée de la création de la queue dans le VI "Server_LabView.vi", ce qui permet à la queue d'avoir le bon type de donnée qu'elle va stocker.

  ![change_data_array_position](\image\change_data_array_position.png)

- Récupérer le "queue out", contenant le queue refnum et le type des données échangé avec la queue , et le "error in". Cette connexion entre le VI du programme de récolte de données et notre programme se fait dans le VI "Server_LabView.vi" en remplaçant le vi "data array refresh.vi" par le VI du programme.

  ![change_queue_position](\image\change_queue_position.png)

- Une fois les données générées il faut, effacer ce qu'il y a dans la queue (s'il y a qq chose) avec le module dequeue element avec le time out à 0. Puis mettre les données générées dans la queue avec le module Enqueue element (sans time out). Comme dans le fichier "data array refresh.vi".



## Protocole utilisé:

Le protocole utilisé est bien évidement TCP/IP. On va détailler ici quelles sont les données échangée et leur rôle. En annexe se trouve une image contenant un diagramme "Diagramme communication" montrant le fonctionnement de l'échange TCP/IP entre python et LabView.

Le client commence par envoyé une trame construite comme suit :

1. Les 4 premiers octets représente la taille de la trame (sans compter ces 4 octets) sous forme d'un signed int 32.
2. La deuxième partie de la trame est composée des coordonnées matricielle des données que l'on veut, chaque coordonné est stocké sur un unsigned char pour prendre le moins de place possible, la coordonnées maximum vaut 15 et est donc inférieur à la valeur maximum pouvant être stockée sur un unsigned char (255).
3. Le server répond avec un trame dont les 4 premiers octets contiennent la taille des données dans la suite de la trame.
4. La deuxième partie de la trame contient les données dans l'ordre des coordonnées envoyées et sous forme d'unsigned double.

## Performance:

Pour une matrice de 15 par 10, on peut monter à 100Hz. On envoit donc 150 double (8 octets) en 0.01s donc la transmission est de 150 * 8 * 100 = 120ko/s.